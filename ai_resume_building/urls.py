from django.urls import path

from ai_resume_building.views import( 
CandidateRegistrationView, ForgotPasswordAPIView, LoginAPIView, RecruiterRegistrationView, ResetPasswordAPIView, ResumeUploadAPIView, 
SendSignupOTPAPIView, VerifyLoginOTPAPIView, VerifySignupOTPAPIView)


urlpatterns = [
     #candidate regristration with email verification
    path("candidate/signup/", CandidateRegistrationView.as_view(), name="candidate-signup",),
    path("recruiter/signup/",RecruiterRegistrationView.as_view(),name="recruiter-signup",),
    #login with password and otp verification
    path("login/", LoginAPIView.as_view(), name="login"),
    #LOGIN OTP VERIFICATION
    path("login/verify-otp/",VerifyLoginOTPAPIView.as_view(),name="verify-login-otp",),
    #signup EMAIL ONLY otp 
    path("signup/send-otp/", SendSignupOTPAPIView.as_view(), name="signup-send-otp"),
    #signup EMAIL otp verification
    path("signup/verify-otp/", VerifySignupOTPAPIView.as_view(), name="signup-verify-otp"),
    #FOR FORGOT PASSWORD
    path("forgot-password/",ForgotPasswordAPIView.as_view(),name="forgot-password",),
    #RESET PASSWORD WITH TOKEN NEED TO VERIFY
    path("reset-password/",ResetPasswordAPIView.as_view(),name="reset-password",),

    #for testing purpose only
    path("resume/upload/",ResumeUploadAPIView.as_view(),name="resume-upload",),

    

   
   
]



