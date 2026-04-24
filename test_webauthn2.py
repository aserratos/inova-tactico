from webauthn import generate_registration_options, options_to_json
from webauthn.helpers import generate_user_handle

opts = generate_registration_options(
    rp_id="inova-tactico.vercel.app",
    rp_name="Test",
    user_id=generate_user_handle(),
    user_name="test@test.com",
    user_display_name="Test User"
)

import json
print(options_to_json(opts))
