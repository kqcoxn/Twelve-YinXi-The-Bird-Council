"""Integration tests for Twelve-YinXi backend."""

import asyncio
import httpx
import sys


BASE_URL = "http://127.0.0.1:8000/api/v1"


async def test_health():
    """Test health endpoint."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        print("[PASS] Health check")


async def test_get_seats():
    """Test getting all seats."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/seats")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 23
        assert data[0]["seat_id"] == "seat_01"
        print(f"[PASS] Get seats: {len(data)} seats")


async def test_get_seat_state():
    """Test getting seat state."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/seats/seat_01/state")
        assert resp.status_code == 200
        data = resp.json()
        assert data["seat_id"] == "seat_01"
        print("[PASS] Get seat state")


async def test_user_profile():
    """Test user profile endpoint."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/user/profile")
        assert resp.status_code == 200
        data = resp.json()
        assert "user_id" in data
        print("[PASS] User profile")


async def test_submit_proposal():
    """Test submitting a proposal."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/council/submit",
            json={
                "user_id": "test_user",
                "session_id": "test_session",
                "user_input": "Should we implement dark mode by default?",
                "category": "general",
                "action_type": "submit_proposal",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "session_id" in data or "id" in data
        print("[PASS] Submit proposal")


async def test_get_session():
    """Test getting session."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/council/session/test_session")
        # May be 404 if session doesn't exist yet, that's ok
        assert resp.status_code in [200, 404]
        print("[PASS] Get session")


async def main():
    """Run all integration tests."""
    print("\n" + "=" * 50)
    print("Integration Tests")
    print("=" * 50 + "\n")

    tests = [
        test_health,
        test_get_seats,
        test_get_seat_state,
        test_user_profile,
        test_submit_proposal,
        test_get_session,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            await test()
            passed += 1
        except Exception as e:
            print(f"[FAIL] {test.__name__}: {e}")
            failed += 1

    print(f"\n{'=' * 50}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'=' * 50}\n")

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
