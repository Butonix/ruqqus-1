# Security

The T_D master cryptographic key was generated with the `secrets` module and is appropriate for cryptographically secure functions.

If you need to sign something, you may access the master key with `os.environ.get("Flask_secret_key")`. The key should be passed directly into cryptographic functions. It should never be saved to a variable.

Attempting to echo, display, save, or otherwise extract the master key is cause for immediate revocation of contributor status.