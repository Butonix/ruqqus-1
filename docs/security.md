# Security

## Master Key

The T_D master cryptographic key was generated with the `secrets` module and is appropriate for cryptographically secure functions.

If you need to sign something, you may access the master key with `os.environ.get("Flask_secret_key")`. The key should be passed directly into cryptographic functions. It should never be saved to a variable.

Attempting to echo, display, save, or otherwise extract the master key is cause for immediate revocation of contributor status.

## CSRF

The following procedures are in place to prevent cross-site request forgery (CSRF).

1. All forms for user input must include the following element, copied exactly:

    {{ "<input type="hidden" name="formkey", value="{{ v.formkey  }}">" }}
    
2. Functions handling incoming POST requests must be decorated with `@validate_formkey`. Above that decorator should be one of `@auth_required`, `@admin_level_required(x)`, or `@is_not_banned`.
