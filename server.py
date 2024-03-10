import uvicorn

if __name__ == '__main__':
    uvicorn.run("account_service.asgi:application",
                reload=True,
                port=8001,
                log_level='info',
                workers=4,
                lifespan='auto')
