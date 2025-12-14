from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.utils import timezone
from .models import *
from .utils import *
from .serializers import *
from apps.accounts.permissions import IsSuperAdmin, IsActiveUser, IsAdminUser
from django.conf import settings
from django.core.mail import EmailMultiAlternatives


# Create your views here.
@api_view(['POST'])
def sign_up(request):
    serializer = SignUpSerializer(data=request.data)
    if serializer.is_valid():
        user = User(
            name=serializer.validated_data.get('name'),
            email=serializer.validated_data.get('email'),
            location=serializer.validated_data.get('location'),
        )
        user.set_password(serializer.validated_data.get('password'))
        mail = user.email
        send_mail_verification(mail)
        user.save()
        return Response({"message": "User successfully registered."}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def send_mail_verification(receiver_email):
    subject = "Welcome to Floating Library"
    message = "Thank you for registering with Floating Library. Your account is under review and will be activated soon."

    from_email = settings.DEFAULT_FROM_EMAIL  
    recipient_list = receiver_email   
    mail = EmailMultiAlternatives(
        subject=subject,
        body=message,
        from_email=from_email,
        to=[recipient_list],
    )
    mail.send(fail_silently=False)
    print("Verification email sent successfully to:", recipient_list)


@api_view(['POST'])
def signin(request):
    serializer = signInSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data.get('email')
    password = serializer.validated_data.get('password')

    user_obj = User.objects.filter(email=email).first()
    if not user_obj:
        return Response(
            {"message": "Invalid email or password."}, status=status.HTTP_401_UNAUTHORIZED)

    if not user_obj.is_active:
        return Response(
            {"message": "Your account is not active. Please verify your email or wait for admin approval."},
            status=status.HTTP_403_FORBIDDEN
        )

    user = authenticate(request, username=email, password=password)
    if not user:
        return Response(
            {"message": "Invalid email or password."}, status=status.HTTP_401_UNAUTHORIZED)

    token = get_tokens_for_user(user)

    return Response(
        {
            "access": token["access_token"],
            "refresh": token["refresh_token"],
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,                 
                "is_superuser": user.is_superuser, 
                "is_staff": user.is_staff,
                "is_active": user.is_active,
                "is_lender": user.is_lender,
                "is_borrower": user.is_borrower,
            }
        },
        status=status.HTTP_200_OK
    )



#edit profile
@api_view(['PATCH'])
@permission_classes([IsActiveUser])
@authentication_classes([JWTAuthentication])
def edit_profile(request):
    user = request.user  
    serializer = UpdateSerializer(user, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(
        {"message": "Profile updated successfully."},
        status=status.HTTP_200_OK
    )



@api_view(['POST'])
@permission_classes([IsActiveUser])
@authentication_classes([JWTAuthentication])
def change_password(request):
    serializer = ChangePasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    old_password = serializer.validated_data['old_password']
    new_password = serializer.validated_data['new_password']

    user = request.user

    if not user.check_password(old_password):
        return Response(
            {"message": "Old password is incorrect."},
            status=status.HTTP_400_BAD_REQUEST
        )

    user.set_password(new_password)
    user.save()

    return Response(
        {"message": "Password changed successfully. Please login again."},
        status=status.HTTP_200_OK
    )



@api_view(['POST'])
def forgot_password(request):
    serializer = RequestResetSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data.get('email')
    
    user = get_object_or_404(User, email=email)
    if user:
        otp = generate_otp()
        hashed_otp = hash_otp(otp)
        Otp.objects.create(
            user=user,
            otp_hash = hashed_otp,
            is_used = False,
            expired_at = otp_expired()
        )
        send_otp_via_email(email, otp)
        return Response({"message": "OTP send seccessfully."}, status=status.HTTP_200_OK)
    

def send_otp_via_email(receiver_email, otp: str):
    subject = "Your OTP Code"
    message = f"Your OTP code is: {otp}. It will expire in 10 minutes."

    from_email = settings.DEFAULT_FROM_EMAIL  
    recipient_list = receiver_email   
    mail = EmailMultiAlternatives(
        subject=subject,
        body=message,
        from_email=from_email,
        to=[recipient_list],
    )
    mail.send(fail_silently=False)
    print("Email sent successfully to:", recipient_list)


@api_view(['POST'])
def verify_otp(request):
    serializer = VerifyOtpSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data['email']
    otp = serializer.validated_data['otp']
    
    try:
        user = User.objects.get(email=email)
        otp_obj = Otp.objects.filter(user=user, is_used=False).order_by('-created_at').first()
    except (User.DoesNotExist, Otp.DoesNotExist):
        return Response({"message": "User or OTP doesn't exist."}, status=status.HTTP_404_NOT_FOUND)
    if otp_obj.expired_at < timezone.now():
        return Response({"message": "OTP expired."}, status=status.HTTP_400_BAD_REQUEST)
    if otp_obj.otp_hash != hash_otp(otp):
        return Response({"message": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({"message": "Your OTP is valid."}, status=status.HTTP_200_OK)


@api_view(["POST"])
def reset_password(request):
    serializer = ResetPasswordSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data["email"]
        new_password = serializer.validated_data["password"]

        try:
            user = User.objects.get(email=email)
            otp_obj = Otp.objects.filter(user=user, is_used=False).first()
        except (User.DoesNotExist, Otp.DoesNotExist):
            return Response({"detail": "Invalid request"}, status=status.HTTP_404_NOT_FOUND)
        if otp_obj.expired_at < timezone.now():
            return Response({"detail": "OTP expired"}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        
        otp_obj.is_used = True
        otp_obj.save()

        return Response({"detail": "Password reset successfully."}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH'])
@permission_classes([IsSuperAdmin])
@authentication_classes([JWTAuthentication])
def make_user_admin(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.role = 'ADMIN'
    user.is_staff = True
    user.is_active = True
    user.save()
    return Response({"message": "User promoted to admin."}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsSuperAdmin, IsAdminUser])
@authentication_classes([JWTAuthentication])
def activate_user_account(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = True
    mail = user.email
    send_mail_activation(mail)
    user.save()
    return Response({"message": "User account activated."}, status=status.HTTP_200_OK)


def send_mail_activation(receiver_email):
    subject = "Account Activation Notice"
    message = "Your account has been activated. You can now log in and start using our services."

    from_email = settings.DEFAULT_FROM_EMAIL  
    recipient_list = receiver_email   
    mail = EmailMultiAlternatives(
        subject=subject,
        body=message,
        from_email=from_email,
        to=[recipient_list],
    )
    mail.send(fail_silently=False)


@api_view(["PATCH"])
@permission_classes([IsSuperAdmin, IsAdminUser])
@authentication_classes([JWTAuthentication])
def deactivate_user_account(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = False
    mail = user.email
    send_mail(mail)
    user.save()
    return Response({"message":"This users account has been deactivated."}, status=status.HTTP_200_OK)

def send_mail(receiver_email):
    subject = "Account Deactivation Notice"
    message = "Your account has been deactivated. Please contact support for more information."

    from_email = settings.DEFAULT_FROM_EMAIL  
    recipient_list = receiver_email   
    mail = EmailMultiAlternatives(
        subject=subject,
        body=message,
        from_email=from_email,
        to=[recipient_list],
    )
    mail.send(fail_silently=False)


# Dashboard stats for counts active users, lenders, and borrowers
@api_view(["GET"])
@permission_classes([IsSuperAdmin])
@authentication_classes([JWTAuthentication])
def dashboard_stats(request):
    return Response({
        "total_users": User.objects.filter(is_active=True).count(),
        "total_lenders": User.objects.filter(is_lender=True, is_active=True).count(),
        "total_borrowers": User.objects.filter(is_borrower=True, is_active=True).count(),
    }, status=status.HTTP_200_OK)



@api_view(['GET'])
@permission_classes([IsSuperAdmin])
@authentication_classes([JWTAuthentication])
def all_user(request):
    # exclude superuser accounts from the list
    # users = User.objects.exclude(is_superuser=True)
    users = User.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsSuperAdmin])
@authentication_classes([JWTAuthentication])
def active_users(request):
    active_users = User.objects.filter(is_active=True)
    serializer = UserSerializer(active_users, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsSuperAdmin])
@authentication_classes([JWTAuthentication])
def inactive_users(request):
    inactive_users = User.objects.filter(is_active=False)
    serializer = UserSerializer(inactive_users, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication])
def my_accounts(request):
    my_accounts = User.objects.filter(user=request.user)
    serializer = UserSerializer(my_accounts)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication])
def all_accounts(request):
    accounts = User.objects.all()
    serializer = UserSerializer(accounts, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)