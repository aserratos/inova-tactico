from webauthn import generate_registration_options
from webauthn.helpers import generate_user_handle

opts = generate_registration_options(
    rp_id="inova-tactico.vercel.app",
    rp_name="Test",
    user_id=generate_user_handle(),
    user_name="test@test.com",
    user_display_name="Test User"
)

import json
print(dir(opts))
from webauthn import options_to_json
try:
    print("options_to_json is available")
except:
    pass
