"""
CORS Diagnostic Tool
"""
import asyncio
import os

import httpx


BASE_URL = os.getenv('BOROFONE_TEST_BASE_URL', 'http://localhost:8000').rstrip('/')
ORIGIN = os.getenv('BOROFONE_TEST_ORIGIN', BASE_URL)


async def test_cors():
    print('\n' + '=' * 60)
    print('CORS Diagnostic Tool')
    print('=' * 60 + '\n')

    print('1. Testing OPTIONS (preflight) request...')
    try:
        async with httpx.AsyncClient() as client:
            response = await client.options(
                f'{BASE_URL}/auth/login',
                headers={
                    'Origin': ORIGIN,
                    'Access-Control-Request-Method': 'POST',
                    'Access-Control-Request-Headers': 'content-type',
                },
            )
            print(f'   Status: {response.status_code}')
    except Exception as exc:
        print(f'   Error: {exc}')

    print('\n2. Testing POST /auth/login...')
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f'{BASE_URL}/auth/login',
                json={'email': 'test@test.com', 'password': 'password'},
                headers={'Origin': ORIGIN},
            )
            print(f'   Status: {response.status_code}')
            print(f'   Set-Cookie present: {"set-cookie" in response.headers}')
    except Exception as exc:
        print(f'   Error: {exc}')

    print('\n3. Testing GET /auth/me...')
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f'{BASE_URL}/auth/me',
                headers={'Origin': ORIGIN},
            )
            print(f'   Status: {response.status_code}')
    except Exception as exc:
        print(f'   Error: {exc}')


if __name__ == '__main__':
    asyncio.run(test_cors())
