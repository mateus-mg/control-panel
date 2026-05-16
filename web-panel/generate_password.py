#!/usr/bin/env python3
"""Generate password hash for admin user."""

import sys
import os

# Add app to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def main():
    if len(sys.argv) < 2:
        password = input("Digite a senha: ").strip()
    else:
        password = sys.argv[1]

    if not password:
        print("Erro: senha não pode ser vazia")
        sys.exit(1)

    hash_value = pwd_context.hash(password)
    print(f"\nHash gerado:\n{hash_value}")
    print(f"\nUse no .env como:\nADMIN_PASSWORD_HASH={hash_value}")


if __name__ == "__main__":
    main()