#!/usr/bin/python3
import http.client
import mimetypes
import datetime
import pprint
import json
import math
import requests
import pandas as pd
from datetime import datetime, timedelta
from functools import reduce

class MyPortfolio(object):
	def __init__(self):
		self.xch_url = "https://v6.exchangerate-api.com/v6/931fba7839f1267eba9ede7f/latest/CAD" #url for cad to inr rate
		self.mf_url = "https://api.mfapi.in/mf/" #mutual fund api
		self.bt_url = "https://blockchain.info/ticker" #bitcoin api
		self.mf_ids = { 
		   "nippon_liquid_fund": 118701,
		   "axis_midcap": 120505,
		   "quant_tax": 120847,
		   "sbi_gold_fund": 119788,
		   "axis_smallcap": 125354,
		   "mo_nasdaq_fof": 145552
		}

	#to get current gold rate in inr
	def get_goldrate(self):
		try:
			now = datetime.today() - timedelta(1)
			today = now.strftime('%Y%m%d')
			conn = http.client.HTTPSConnection("www.goldapi.io")
			payload = ''
			headers = {
			  'x-access-token': 'goldapi-19cthukkyajvg1-io',
				'Content-Type': 'application/json'
				}
			conn.request("GET", "/api/XAU/INR/{}".format(today), payload, headers)
			res = conn.getresponse()
			data = json.loads(res.read().decode('utf-8'))
			pre_pergram = math.floor(data['prev_close_price']/28.34952)
			pergram = math.floor(data['price']/28.34952)
			data.update({'gram_rate':pergram, 'prev_gram_rate':pre_pergram})
			diffs = data['prev_gram_rate'] - data['gram_rate']
			gold_data = { 
				  'success': True,
				  'gram_rate': data['gram_rate'], 
				  'prev_gram_rate': data['prev_gram_rate'], 
				  'date': data['date'],
				  'difference': diffs if diffs < 0 else -abs(diffs)
				   }
		except Exception as e:
			return {"success": False, "error": str(e)}
		return gold_data

	def get_currencyrate(self):
		# Making request
		try:
			response = requests.get(self.xch_url)
			exch_data = response.json()

			base_code = exch_data["base_code"]
			exch_date = exch_data["time_last_update_utc"]
			cad_to_inr = exch_data["conversion_rates"]["INR"]
			cad_to_usd = exch_data["conversion_rates"]["USD"]

			curr_exch_rate = {
				   'success': True,
				   'base_code': base_code,
				   'date': exch_date,
				   'cad_to_usd': cad_to_usd,
				   'cad_to_inr': cad_to_inr
				  }
		except Exception as e:
			return {"success": False, "error": str(e)}
		return curr_exch_rate

	def _get_mf_df(self, mfid, days):
		try:
			url = f"https://api.mfapi.in/mf/{mfid}"
			resp = requests.get(url)
			df = pd.DataFrame.from_dict(resp.json()["data"])
			as_types = {'date': 'datetime64[ns]', "nav": float}
			df = df.astype(as_types)
			df = df.rename(columns = {'nav': f'{mfid}'})
			
			last_5 = datetime.now() - timedelta(days=days)
			current_date = datetime.now().strftime("%Y-%m-%d")
			last_5_date = last_5.strftime("%Y-%m-%d")

			filtered_df = df.loc[(df['date'] > last_5_date) & (df['date'] < current_date)]
		except Exception as e:
			return None
		return filtered_df

	#mutual funds
	def get_mf_nav_rates(self):
		try:
			mf_ids2 = {y:x for x,y in self.mf_ids.items()}
			frames = []
			for k, v in self.mf_ids.items():
				frames.append(self._get_mf_df(v, 5))

			fin_df = reduce(lambda x, y: pd.merge(x, y, on = 'date'), frames)
			fin_df1 = fin_df.set_index('date').T
			out = fin_df1.to_json(date_format = 'iso')
			out = reduce(lambda x, y: x.replace(str(y), mf_ids2[y]), mf_ids2, out)
			mf_data = json.loads(out)

			key_list = sorted(mf_data.keys(), reverse=True)
			val_list = []
			for i in range(2): #pick first two
				val_list.append(mf_data[key_list[i]])

			nav_diffs = { k: round(v - val_list[1][k],3) for k, v in val_list[0].items() }
		except Exception as e:
			return {"success": False, "error": str(e)}
		return { "success": True, "mf_portfolio": { key_list[0]:nav_diffs} }

	#bitcoin to cad
	def get_bitcoin_rates(self):
		resp = requests.get(self.bt_url)
		fifteen_min = resp.json()["CAD"]["15m"]
		last = resp.json()["CAD"]["last"]
		return { "bitcoin": {"fifteen_min": fifteen_min, "last": last}}


if __name__ == '__main__':
	mp = MyPortfolio()
	print(mp.get_goldrate())
	print(mp.get_currencyrate())
	print(mp.get_mf_nav_rates())
	print(mp.get_bitcoin_rates())