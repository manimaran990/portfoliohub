#!/usr/bin/python3
import http.client
import mimetypes
import datetime
import pprint
import json
import math
import requests
from datetime import datetime, timedelta
from functools import reduce
import pytz
import copy
import math
import re
from bs4 import BeautifulSoup
from fastapi.responses import HTMLResponse


class MyPortfolio(object):
	def __init__(self):
		today = datetime.today()
		curr_date = today.strftime("%d-%b-%Y")
		prev_date = (today - timedelta(1)).strftime("%d-%b-%Y")
		self.xch_url = "https://v6.exchangerate-api.com/v6/931fba7839f1267eba9ede7f/latest/CAD" #url for cad to inr rate
		self.curr_mf_url = "https://www.amfiindia.com/spages/NAVAll.txt"
		self.prev_mf_url = f"https://portal.amfiindia.com/DownloadNAVHistoryReport_Po.aspx?tp=1&frmdt={prev_date}&todt={prev_date}"
		self.bt_url = "https://api.blockchain.com/v3/exchange/tickers/" #bitcoin api
		self.mf_ids = { 
		   "nippon_liquid_fund": 118701,
		   "axis_midcap": 120505,
		   "quant_tax": 120847,
		   "sbi_gold_fund": 119788,
		   "axis_smallcap": 125354,
		   "mo_nasdaq_fof": 145552
		}
		self.headers = {
			"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:84.0) Gecko/20100101 Firefox/84.0",
		}

	def dict_subtract(self, dict1, dict2):
		return { k: round(v - dict2[k], 2)  for k,v in dict1.items() }

	#to get current gold rate in inr
	def get_goldrate(self):
		try:
			page = requests.get('https://www.kitco.com/gold-price-today-india/index.html', headers=self.headers).text
			soup = BeautifulSoup(page, 'html.parser').find_all(class_="table-price--body-table--overview-detail")
			return HTMLResponse(content=soup[0], status_code=200)
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

	def _get_mf_df(self):
		try:
			curr = requests.get(self.curr_mf_url).text
			prev = requests.get(self.prev_mf_url).text

			#reverse mf_ids dictionary
			mf_names = { str(v): k for k, v in self.mf_ids.items() }

			#current mf nav changes
			curr_lst = []
			for k,v in self.mf_ids.items():
				line = re.search(f'{v}.*', curr).group(0)
				lst = line.strip().split(';')
				date = {lst[5]}
				curr_lst.append( (lst[0], float(lst[4]) ) )

			#previous mf nav changs
			prev_lst = [] 
			for k,v in self.mf_ids.items():
				line = re.search(f'{v}.*', prev).group(0)
				lst = line.strip().split(';')
				date = {lst[7]}
				prev_lst.append( (lst[0], float(lst[4]) ) )

			curr_dict = dict(curr_lst)
			prev_dict = dict(prev_lst)
			diff_dict = self.dict_subtract(curr_dict, prev_dict)

			keys = diff_dict.keys()

			fin_dict = {}
			for k in keys:
				fin_dict[k] = { "name": mf_names[k],"current" : curr_dict[k], "prev": prev_dict[k], "diff": diff_dict[k] }
		except Exception as e:
			return str(e)
		return fin_dict

	#mutual funds
	def get_mf_nav_rates(self):
		try:
			mf_changes = self._get_mf_df()
		except Exception as e:
			return {"success": False, "error": str(e)}
		return { "success": True, "mf_portfolio": mf_changes }

	#bitcoin to cad
	def get_bitcoin_rates(self):
		tickers = ['ETH-USD', 'BTC-USD']
		keys = ['symbol', 'last_trade_price']
		crypt_data = []
		for ticker in tickers:
			resp = requests.get(self.bt_url+ticker).json()
			crypt_data.append(tuple([ resp[k] for k in keys ]))

		crypt_usd = dict(tuple([ tuple(k) for k in crypt_data ]))
		crypt_cad = copy.deepcopy(crypt_usd)
		for k in tickers:
			crypt_cad[k] = math.floor(crypt_usd[k] * requests.get("https://v6.exchangerate-api.com/v6/931fba7839f1267eba9ede7f/latest/USD").json()['conversion_rates']['CAD'])

		return { "success": True,  "cyptos":  crypt_cad}


if __name__ == '__main__':
	mp = MyPortfolio()
	# print(mp.get_goldrate())
	# print(mp.get_currencyrate())
	print(mp.get_mf_nav_rates())
	# print(mp.get_bitcoin_rates())