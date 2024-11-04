import secrets


JWT_SECRET = secrets.token_hex(32)

# Create token blacklist - this would need to move to a distributed cache in prod
jwt_blocklist = set()