"""
실제 토큰 디버깅 스크립트
실제 브라우저에서 가져온 토큰을 분석합니다.
"""
import base64
import json
import sys


def debug_real_token(token: str):
    """실제 토큰을 상세히 디버깅합니다."""
    print("=" * 60)
    print("SUPABASE TOKEN DEBUG")
    print("=" * 60)

    print("Original token:")
    print(f"  Length: {len(token)}")
    print(f"  Starts with 'base64-': {token.startswith('base64-')}")
    print(f"  First 100 chars: {token[:100]}...")
    print(f"  Last 50 chars: ...{token[-50:]}")

    # base64- prefix 제거
    if token.startswith("base64-"):
        token = token[7:]
        print("\nAfter removing 'base64-' prefix:")
        print(f"  Length: {len(token)}")

    # Base64 디코딩 시도
    print(f"\n{'='*60}")
    print("BASE64 DECODING ATTEMPTS")
    print("=" * 60)

    methods = [
        (
            "URL-safe base64",
            lambda t: base64.urlsafe_b64decode(t + "=" * (4 - len(t) % 4)),
        ),
        ("Standard base64", lambda t: base64.b64decode(t + "=" * (4 - len(t) % 4))),
        ("Without padding", lambda t: base64.urlsafe_b64decode(t)),
        ("Standard without padding", lambda t: base64.b64decode(t)),
    ]

    decoded_data = None
    successful_method = None

    for method_name, decode_func in methods:
        try:
            decoded = decode_func(token)
            print(f"✓ {method_name}: SUCCESS")
            print(f"  Decoded length: {len(decoded)} bytes")

            # UTF-8 디코딩 시도
            try:
                text = decoded.decode("utf-8")
                print("  UTF-8 decoding: SUCCESS")
                print(f"  Text preview: {text[:200]}...")

                # JSON 파싱 시도
                try:
                    json_data = json.loads(text)
                    print("  JSON parsing: SUCCESS")
                    decoded_data = json_data
                    successful_method = method_name
                    break
                except json.JSONDecodeError as e:
                    print(f"  JSON parsing: FAILED - {e}")
                    print("  Trying to find JSON boundaries...")

                    # JSON이 잘렸거나 이어진 경우 확인
                    if text.count("{") != text.count("}"):
                        print(
                            f"  Unbalanced braces: {{ count={text.count('{')} }} count={text.count('}')}"
                        )

            except UnicodeDecodeError as e:
                print(f"  UTF-8 decoding: FAILED - {e}")
                print(f"  Raw bytes preview: {decoded[:100]}")

        except Exception as e:
            print(f"✗ {method_name}: FAILED - {e}")

    # 성공한 경우 JSON 데이터 분석
    if decoded_data:
        print(f"\n{'='*60}")
        print("JSON STRUCTURE ANALYSIS")
        print("=" * 60)

        print("Top-level keys:")
        for key in decoded_data.keys():
            value = decoded_data[key]
            if isinstance(value, str):
                print(f"  {key}: '{value[:50]}...' (string, length={len(value)})")
            elif isinstance(value, dict):
                print(f"  {key}: dict with {len(value)} keys")
            elif isinstance(value, list):
                print(f"  {key}: list with {len(value)} items")
            else:
                print(f"  {key}: {type(value)} = {value}")

        # access_token 찾기
        if "access_token" in decoded_data:
            access_token = decoded_data["access_token"]
            print("\n✓ Found access_token!")
            print(f"  Length: {len(access_token)}")
            print(f"  Preview: {access_token[:100]}...")

            # JWT인지 확인
            parts = access_token.split(".")
            if len(parts) == 3:
                print("  ✓ Looks like JWT (3 parts)")

                # Header 디코딩
                try:
                    header_b64 = parts[0] + "=" * (4 - len(parts[0]) % 4)
                    header = json.loads(base64.urlsafe_b64decode(header_b64))
                    print(f"  JWT Header: {header}")
                except:
                    print("  JWT Header: Failed to decode")

                # Payload 디코딩
                try:
                    payload_b64 = parts[1] + "=" * (4 - len(parts[1]) % 4)
                    payload = json.loads(base64.urlsafe_b64decode(payload_b64))
                    print(f"  JWT Payload keys: {list(payload.keys())}")

                    # 중요 필드 확인
                    important_fields = [
                        "sub",
                        "email",
                        "app_metadata",
                        "user_metadata",
                        "role",
                        "exp",
                    ]
                    for field in important_fields:
                        if field in payload:
                            value = payload[field]
                            if isinstance(value, dict):
                                print(
                                    f"    {field}: dict with keys {list(value.keys())}"
                                )
                            else:
                                print(f"    {field}: {value}")

                except Exception as e:
                    print(f"  JWT Payload: Failed to decode - {e}")
            else:
                print(f"  ✗ Not a JWT (has {len(parts)} parts, expected 3)")

        # user 객체 찾기
        if "user" in decoded_data:
            user = decoded_data["user"]
            print("\n✓ Found user object!")
            if isinstance(user, dict):
                print(f"  User keys: {list(user.keys())}")

                # 중요 사용자 필드 확인
                user_fields = ["id", "email", "app_metadata", "user_metadata"]
                for field in user_fields:
                    if field in user:
                        value = user[field]
                        if isinstance(value, dict):
                            print(f"    {field}: dict with keys {list(value.keys())}")
                        else:
                            print(f"    {field}: {value}")

    print(f"\n{'='*60}")
    if successful_method:
        print(f"SUCCESS: Use {successful_method} for decoding")
    else:
        print("FAILED: Unable to decode token")
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_real_token.py <your_actual_token>")
        print("\nExample:")
        print("python debug_real_token.py 'base64-eyJhY2Nlc3NfdG9rZW4i...'")
        print("\nPaste your actual token from browser Application tab:")
        print("Application → Storage → Cookies → sb-{project}-auth-token.0")
        sys.exit(1)

    actual_token = sys.argv[1]
    debug_real_token(actual_token)
