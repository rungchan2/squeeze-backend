"""
토큰 형식 디버깅 스크립트
Supabase 토큰의 실제 형식을 확인합니다.
"""
import base64
import json
import sys


def debug_token(token: str):
    """토큰을 디버깅합니다."""
    print("=== Token Debug ===")
    print(f"Original token length: {len(token)}")
    print(f"First 50 chars: {token[:50]}...")
    print(f"Last 20 chars: ...{token[-20:]}")

    # base64- prefix 확인
    if token.startswith("base64-"):
        print("\n✓ Token has 'base64-' prefix")
        token = token[7:]
        print(f"Token without prefix length: {len(token)}")

    # Bearer prefix 확인
    if token.startswith("Bearer "):
        print("\n✓ Token has 'Bearer ' prefix")
        token = token[7:]

    # JWT 형식 확인 (3부분으로 나뉘어져야 함)
    parts = token.split(".")
    print(f"\n✓ Token parts count: {len(parts)}")

    if len(parts) == 3:
        print("✓ Token looks like JWT (3 parts)")

        # 각 부분 디코딩 시도
        for i, part in enumerate(parts):
            print(f"\n--- Part {i+1} ---")
            print(f"Length: {len(part)}")
            print(f"Preview: {part[:30]}...")

            if i < 2:  # header와 payload만 디코딩
                try:
                    # Base64 padding 추가
                    padded = part + "=" * (4 - len(part) % 4)
                    decoded = base64.urlsafe_b64decode(padded)
                    data = json.loads(decoded)
                    print("✓ Decoded successfully:")
                    print(json.dumps(data, indent=2))
                except Exception as e:
                    print(f"✗ Failed to decode: {e}")

                    # 일반 base64 시도
                    try:
                        decoded = base64.b64decode(part + "=" * (4 - len(part) % 4))
                        print(f"✓ Standard base64 decoded: {decoded[:100]}")
                    except:
                        print("✗ Not standard base64 either")

    else:
        print(f"✗ Token doesn't look like JWT (expected 3 parts, got {len(parts)})")

        # 토큰이 추가로 인코딩되어 있는지 확인
        print("\n✓ Checking if token is additionally encoded...")

        try:
            # Base64 디코딩 시도
            decoded = base64.b64decode(token + "=" * (4 - len(token) % 4))
            print("✓ Base64 decoded successfully")
            print(f"Decoded length: {len(decoded)}")
            print(f"Decoded preview: {decoded[:100]}")

            # 디코딩된 값이 JWT인지 확인
            if b"." in decoded:
                decoded_str = decoded.decode("utf-8", errors="ignore")
                decoded_parts = decoded_str.split(".")
                if len(decoded_parts) == 3:
                    print(
                        f"✓ Decoded value is JWT! Actual token: {decoded_str[:50]}..."
                    )
                    return debug_token(decoded_str)  # 재귀적으로 디버깅

        except Exception as e:
            print(f"✗ Not base64 encoded: {e}")

        # 다른 가능성 확인
        print("\n✓ Other checks:")
        print(f"Contains 'ey': {'ey' in token}")
        print(f"Contains '.': {'.' in token}")
        print(f"Is alphanumeric: {token.replace('-', '').replace('_', '').isalnum()}")


if __name__ == "__main__":
    # 커맨드라인 인자로 토큰 받기
    if len(sys.argv) < 2:
        print("Usage: python debug_token.py <token>")
        print("Example: python debug_token.py base64-eyJhbGc...")
        sys.exit(1)

    token = sys.argv[1]
    debug_token(token)
