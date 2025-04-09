# import jwt
# from rest_framework.authentication import BaseAuthentication, get_authorization_header
# from rest_framework.permissions import BasePermission
# from rest_framework.exceptions import AuthenticationFailed

# class CustomSSOAuthentication(BaseAuthentication, BasePermission):
#     """
#     Allows access only to users with a valid SSO token.
#     """

#     def extract_token(self, request):
#         auth_header = get_authorization_header(request).split()
#         if not auth_header or auth_header[0].lower() != b'bearer':
#             return None
#         if len(auth_header) == 1 or len(auth_header) < 2:
#             return None
#         return auth_header[1]

#     def authenticate(self, request):
#         print("DEBUG: authenticate() called")
#         token = self.extract_token(request)
#         if not token:
#             print("DEBUG: No token found")
#             return None

#         try:
#             decoded_token = jwt.decode(token, 'sso_secret_key_for_jwt_decoding', algorithms=['HS256'])
#             print(f"DEBUG: Token Decoded - {decoded_token}")

#             request.email = decoded_token.get('email')
#             print(f"DEBUG: request.email set to {request.email}")

#             return (None, token)

#         except jwt.ExpiredSignatureError:
#             print("DEBUG: Token expired")
#             raise AuthenticationFailed('Token has expired')
#         except jwt.InvalidTokenError:
#             print("DEBUG: Invalid token")
#             raise AuthenticationFailed('Invalid token')

#     def has_permission(self, request, view):
#         """
#         Checks if the user information is attached to the request object.
#         """
#         # Check if authentication was successful
#         auth_result = self.authenticate(request)
#         if not auth_result:
#             return False

#         user, token = auth_result  # Unpack the result

#         # Ensure the user attributes are set
#         if not all([hasattr(request, attr) for attr in ['first_name', 'last_name', 'email']]):
#             return False

#         # You can perform additional permission checks based on user information
#         return True  # Assuming all authenticated users have permission