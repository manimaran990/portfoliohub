from fastapi import FastAPI
from portfolio import MyPortfolio

app = FastAPI()
mp = MyPortfolio()

@app.get("/getgoldrate")
async def goldrate():
    return mp.get_goldrate()

@app.get("/getexchrate")
async def exchrate():
    return mp.get_currencyrate()

@app.get("/getMFchanges")
async def getMFchange():
    return mp.get_mf_nav_rates()

@app.get("/getbtrate")
async def getBTrate():
    return mp.get_bitcoin_rates()