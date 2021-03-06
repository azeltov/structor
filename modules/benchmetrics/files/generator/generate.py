#!/usr/bin/python

# run setupGenerate.sh before trying this.

import calendar
import sys, math, random, time
import numpy
import os
import scipy
import scipy.stats
import string
import uuid

from collections import namedtuple
from datetime import datetime, timedelta
from getopt import getopt
from os.path import join as path_join
from zipf import zipf

os.environ['TZ']='UTC'

basedir = os.path.dirname(__file__)

from faker import Factory
faker = Factory.create()

class GeneratorOutput(object):
	store = None
	topic = None

	@staticmethod
	def factory(topic, child, extras):
		if "kafka_producer" in extras:
			return KafkaGeneratorOutput(topic, child)
		else:
			return FileGeneratorOutput(topic, child)

class KafkaGeneratorOutput(GeneratorOutput):
	store = None
	topic = None

	def __init__(self, topic, child):
		self.store = extras["kafka_producer"]
		self.topic = topic

	def write(self, message):
		self.store.send(self.topic, bytes(message))

	def close(self):
		self.store.flush()

class FileGeneratorOutput(GeneratorOutput):
	store = None

	def __init__(self, topic, child):
		file = topic + ".%09d.txt" % child
		self.store = open(file, "w")

	def write(self, message):
		self.store.write(message)
		return self.store.write("\n")

	def close(self):
		self.store.close()

def parse_into(f, ttype, separator='|'):
	return [ttype._make(l.strip().split(separator)) for l in open(f)]

def to_datetime(d):
	return datetime.strptime(d, "%Y-%m-%d")

def end_of_month(d):
        d = to_datetime(d)
        (w,m) = calendar.monthrange(d.year, d.month)
	return d + timedelta(days = m-d.day)

earliest_date = to_datetime('2014-01-01')
latest_date = to_datetime('2015-12-31')

def transaction(i, aid, edate, same_month=False):
	global faker, earliest_date, latest_date
	transaction_id = 1000000000 + i
	effective_date = faker.date_time_between(start_date=to_datetime(edate), end_date=end_of_month(edate)).strftime("%Y-%m-%d")
	entry_date = effective_date 
	post_date = effective_date
	tc = random.choice(transaction_types)
	transaction_code = tc.transaction_code
	transaction_type = tc.transaction_type
	amount = random.randint(0, 100000000)/100.0
	quantity = random.randint(0, 1000) / 100.0
	product_category = "%s%d" % (random.choice(string.ascii_lowercase),random.randint(0, 999))
	last_date = latest_date
	if same_month:
		last_date = end_of_month(effective_date)
	td = faker.date_time_between(start_date=to_datetime(effective_date), end_date=last_date)
	test_date = td.strftime("%Y-%m-%d")
	test_datetime = td.strftime("%a %d %b %Y %I:%M:%S %p %z")
	transaction_location = faker.zipcode()
	transaction_state = faker.state_abbr()
	sales_person_id = random.randint(0, 10000000)
	sales_person_name = faker.name()
	random_string = faker.paragraph()
	random_number = random.randint(0, 10000000) / 23.0
	original_ccy = faker.currency_code()
	reporting_ccy = faker.currency_code()
	account_id = aid 
	return [transaction_id, entry_date, post_date, transaction_code, transaction_type, amount, quantity, product_category, test_date, test_datetime, transaction_location, transaction_state, sales_person_id, sales_person_name, random_string, random_number, original_ccy, reporting_ccy, account_id, effective_date]

def account(i, edate, same_month=False):
	global faker, earliest_date, latest_date
	account_id = 1000000000 + i
	account_number = faker.ssn() 
	at = random.choice(account_types)
	account_code = at.account_code
	account_type = at.account_type
	account_subtype = at.account_subtype
	account_subtype2 = at.account_subtype2
	account_description = faker.paragraph()
	card_number = faker.credit_card_number()
	card_security_id = faker.credit_card_security_code()
	last_date = latest_date
	if same_month:
		last_date = end_of_month(edate)
	effective_date = faker.date_time_between(start_date=to_datetime(edate), end_date=last_date).strftime("%Y-%m-%d")
	return [account_id, account_number, account_code, account_type, account_subtype, account_subtype2, account_description, card_number, card_security_id, effective_date]

def credit_card_with_dashes(faker):
	x = faker.credit_card_number()
	l = len(x)
	if l == 12:
		return "-".join([ x[0:4], x[4:6], x[6:8], x[8:12] ])
	if l == 13:
		return "-".join([ x[0:4], x[4:7], x[7:9], x[9:13] ])
	if l == 14:
		return "-".join([ x[0:4], x[4:7], x[7:10], x[10:14] ])
	if l == 15:
		return "-".join([ x[0:4], x[4:8], x[8:11], x[11:15] ])
	if l == 16:
		return "-".join([ x[0:4], x[4:8], x[8:12], x[12:16] ])

def customer_accounts(i, edate):
	global faker, earliest_date, latest_date
	customer_id = 1000000000 + i
	customer_type = random.choice(customer_types)
	ssn = faker.ssn()
	company = faker.company()
	customer_name_prefix = faker.prefix()
	customer_name_last = faker.last_name()
	customer_name_first = faker.first_name()
	customer_name_suffix = faker.suffix()
	addr_street_number = faker.building_number()
	addr_street_name = faker.street_name()
	addr_line_2 = faker.secondary_address()
	addr_city = faker.city()
	addr_state = faker.state_abbr()
	addr_postal_code = faker.zipcode_plus4()
	email = faker.email()
	phone_home = faker.phone_number()
	phone_cell = faker.phone_number()
	phone_work = faker.phone_number()
	phone_work_ext = faker.random_digit_not_null_or_empty()
	date_of_birth = faker.date_time_between(start_date='-50y', end_date='-20y').strftime("%Y-%m-%d")
	driver_lic = faker.ean13()
	sex = random.choice(['M', 'F'])
	# no randomization
	effective_date = edate
	return [customer_id, customer_type, ssn, company, customer_name_prefix, customer_name_last, customer_name_first, customer_name_suffix, 
	addr_street_number, addr_street_name, addr_line_2, addr_city, addr_state, addr_postal_code, email, phone_home, phone_cell, phone_work, phone_work_ext,
	date_of_birth, driver_lic, sex, effective_date]

def write_rows(f, rs):
	for r in rs:
		f.write('|'.join(map(str,r)) + "\n")

def fake_accounts(scale=1, child=0, extras=None):
	global earliest_date

	account_type = namedtuple('AccountType', ['account_code', 'account_type', 'account_subtype', 'account_subtype2', 'effective_date'])
	transaction_type = namedtuple('TransactionType', ['transaction_code', 'transaction_type'])
	account_types = parse_into(path_join(basedir, "../data/account_types.dat"), account_type)
	transaction_types = parse_into(path_join(basedir, "../data/transaction_types.dat"), transaction_type) 
	customer_types = ["corporate", "individual"]

	start_rows = 0
	end_rows = 100
	child = 0
	scale = 1
	if (child >= scale):
		print "Argument mismatch: child cannot be greater than scale"
		return 1
	if (scale > 1):
		# the distribution below corresponds to approx 100kb per customer
		start_rows = child*1024*100
		end_rows = (child+1)*1024*100
	max_accounts = 13
	max_txns = 20
	reseed_split = 100
	z1 = None
	z2 = None
	total = 0

	fname = lambda t : "%s.dat.%d" % (t, child)

	tbl_customers = open(fname("customers"), "w")
	tbl_accounts = open(fname("accounts"), "w")
	tbl_c_accounts = open(fname("customer_accounts"), "w")
	tbl_txns = open(fname("transactions"), "w")
	totals = 0
	if child == 0:
		write_rows(open(fname("account_types"), "w"), map(list, account_types))
		write_rows(open(fname("transaction_types"), "w"), map(list, transaction_types))
	for i in xrange(start_rows, end_rows):
		# reseed every 100 rows so that we can split the gen
		if (i % reseed_split == 0):
			random.seed(i)
			faker.seed(i)
			z1 = zipf(max_accounts, 1)
			z2 = zipf(max_txns, 1.1)
		edate = faker.date_time_between(start_date=earliest_date).strftime("%Y-%m-%d")
		# Customer has > 1 account, account as > 1 txn
		c_s = customer_accounts(i, edate)
		# one account in the same month
		zv = z1.next();
		a_s = [account(max_accounts*i+j, edate, zv == 1) for (k,j) in enumerate(xrange(0,zv-1))]
		# customer_id + first col is account_id, last col is effective_date
		ac_s = [[c_s[0], a[0], a[-1]] for a in a_s]
		# one txn in the same month
		zv = z2.next();
		t_s = [transaction(max_accounts*i+max_txns*j+k, a[1], a[-1], zv == 1) for (j,a) in enumerate(ac_s) for k in xrange(0, zv-1)]
		totals += len(t_s) 
		write_rows(tbl_customers, [c_s])
		write_rows(tbl_accounts, a_s)
		write_rows(tbl_c_accounts, ac_s)
		write_rows(tbl_txns, t_s)
		#print "Written %d transactions for %d customers" % (totals, i-start_rows)
	return 0

# Supported journies:
#  Mobile -> campaign -> evaluate -> abandon
#  Mobile -> campaign -> evaluate -> convert
#  Mobile -> campaign -> evaluate -> defer -> wait 1-8 hours -> Desktop -> search -> convert
#  Mobile -> search -> abandon
#  Mobile -> search -> convert
#  Desktop -> campaign -> evaluate -> abandon
#  Desktop -> campaign -> evaluate -> convert
#  Desktop -> search -> abandon
#  Desktop -> search -> convert
# Order:
#  (1) figure out mobile versus desktop
#  (2) Figure out search versus campaign
#  (3) For campaign, evaluate the campaign relative to user
#  (4) Convert or Abandon
# Events will run over a 3 month period
# Num Journies = 250000 per segment
# Explicit breakdown of mobile versus desktop.
# Base mobile conversion rate = 1%
# Base desktop conversion rate = 4%
# Potential customer pool = scale * 20000
# Device ownership = 1xMobile + 1xDesktop
# 20 campaigns per month (120 total)
# Mobile mix:
#  3 overlapping beta distributions
#  1 large distribution centered at noon for desktop
#  2 smaller distributions for mobile
def fake_multidevice(scale=1, child=0, extras=None):
	num_users = 1000
	num_journies = 20000
	num_campaigns = 20
	num_products = 100
	base_desktop_sale_chance = 0.04
	base_mobile_sale_chance = 0.01
	chance_switch_mobile_to_desktop = 0.75

	# The campaigns need to be the same everywhere.
	random.seed(0)

	# Static load script assets.
	load_script = """#!/bin/sh

set -x

for f in campaigns clickstream sales users; do
	hdfs dfs -mkdir -p /apps/hive/warehouse/multichannel.db/$f
	hdfs dfs -copyFromLocal -f fake_$f* /apps/hive/warehouse/multichannel.db/$f
done
"""
	with open("fake_load.sh", "w") as fd:
		fd.write(load_script)

	# Table DDL
	table_ddl = """
drop database if exists multidevice cascade;
create database multidevice;
use multidevice;

create table campaigns(
	campaign_id int,
	sex_preference string,
	mobile_optimized boolean,
	optimal_hour int,
	promoted_product_id int
) row format delimited fields terminated by '|';

create table clickstream(
	click_time timestamp,
	ip string,
	product_id int,
	campaign_id int,
	cookie string,
	platform string
) row format delimited fields terminated by '|';

create table sales(
	sale_time timestamp,
	customer_id int,
	product_id int,
	promotion_id int,
	cookie string
) row format delimited fields terminated by '|';

create table users(
	customer_id int,
	customer_name string,
	customer_sex string,
	customer_ccn string,
	customer_city string,
	customer_state string,
	customer_zip string,
	customer_email string,
	customer_phone string
) row format delimited fields terminated by '|';
"""
	with open("create_multidevice_database.sql", "w") as fd:
		fd.write(table_ddl)

	# Generate some campaigns and record them.
	campaigns = []
	for i in xrange(0, num_campaigns):
		campaigns.append( {
			"id"               : i + 1,
			"sex_preference"   : random.choice(['M', 'F']),
			"mobile_optimized" : random.choice([True, False]),
			"optimal_hour"     : int(random.uniform(8, 18)),
			"promoted_product" : int(random.uniform(0, num_products))
		} )
	output = GeneratorOutput.factory("fake_campaigns", child, extras)
	for c in campaigns:
		record = [ c["id"], c["sex_preference"], c["mobile_optimized"], c["optimal_hour"], c["promoted_product"] ]
		record = [ str(x) for x in record ]
		output.write('|'.join(record))

	# Break out of the sameness.
	random.seed(child)

	# Create users.
	users = []

	output = GeneratorOutput.factory("fake_users", child, extras)
	for i in xrange(0, num_users):
		user_id = str(i + (num_users * child))
		sex = random.choice(['M', 'F'])
		name = None
		if sex == "M":
			name = " ".join([faker.first_name_male(), faker.first_name_male()])
		else:
			name = " ".join([faker.first_name_female(), faker.first_name_female()])
		credit_card = credit_card_with_dashes(faker)
		addr_city = faker.city()
		addr_state = faker.state_abbr()
		addr_postal_code = faker.zipcode()
		email = faker.email()
		phone_cell = faker.phone_number()
		record = [ user_id, name, sex, credit_card, addr_city, addr_state, addr_postal_code, email, phone_cell ]
		users.append(record)
		output.write('|'.join(record))
	output.close()

	# Setup distributions.
	numpy.random.seed(seed=child)
	mobile_1 = scipy.stats.beta(2, 5)
	mobile_2 = scipy.stats.beta(2, 1)
	desktop_1 = scipy.stats.beta(2, 2)
	time_distribution = scipy.stats.beta(2, 2)

	# Create random journies.
	cookies = {}
	ip_addresses = {}
	clicks = []
	sales = []
	num_mobile_switches = 0
	for i in xrange(0, num_journies):
		# Tracking ID (to measure effectiveness of multi-device detection)
		tracking_id = i + (num_journies * child)

		# When?
		date_min = datetime(2016, 04, 01, 0, 0)
		date_max = datetime(2016, 06, 30, 23, 59)
		date_time = faker.date_time_between(start_date=date_min, end_date=date_max)
		time_offset = time_distribution.rvs()

		# Get the specific time in H/M/S.
		minutes = time_offset * 1440
		hours = int(minutes / 60)
		seconds = int(minutes % 1 * 60)
		minutes = int(minutes - hours * 60)
		date_time.replace(hour=hours, minute=minutes, second=seconds)

		# Mobile or desktop? Get the CDFs of the 3 distributions and pick among them.
		cdfs = [ desktop_1.cdf(time_offset), mobile_1.cdf(time_offset) / 4, mobile_2.cdf(time_offset) / 4 ]
		choice = random.uniform(0, sum(cdfs))
		platform = "mobile"
		if choice <= cdfs[0]:
			platform = "desktop"

		# Organic search or promotion?
		organic = True
		campaign = None
		if random.random() < 0.25:
			organic = False
			campaign = random.choice(campaigns)

		# The user in question. This is hidden within the clickstream, visible in the orders table.
		user_offset = int(random.uniform(0, num_users))
		user_id = user_offset + (num_users * child)

		# Cookie ID. We track these in case they are re-used.
		cookie_id = assign_cookie(cookies, user_id, platform)

		# IP addresses. These are stable per user.
		if user_id not in ip_addresses:
			ip_addresses[user_id] = [ None, None ]
		offset = 0 if platform == "desktop" else 1
		if ip_addresses[user_id][offset] == None:
			ip_addresses[user_id][offset] = random_ip_address(user_id)
		ip_address = ip_addresses[user_id][offset]

		# User visits a few pages. Number of pages is gamma distributed but more focused for campaigns.
		if campaign:
			num_pages = int(random.gammavariate(1, 3) + 1)
		else:
			num_pages = int(random.gammavariate(2, 3) + 1)

		# Seed the product ID.
		if campaign:
			original_product_id = campaign['promoted_product']
			campaign_id = campaign['id']
		else:
			original_product_id = None
			campaign_id = 0
		click_time = date_time
		for j in range(0, num_pages):
			if original_product_id != None:
				product_id = original_product_id
				original_product_id = None
			else:
				product_id = random.randint(0, num_products)
			click = [ click_time, ip_address, product_id, campaign_id, cookie_id, platform, tracking_id ]
			click = [ str(x) for x in click ]
			think_time = random.randint(0, 45)
			click_time = click_time + timedelta(seconds=think_time)

			# We buffer these up and sort by time before outputting.
			clicks.append(click)

		# Determine if we've made a sale.
		if platform == "desktop":
			sale_chance = base_desktop_sale_chance
		else:
			sale_chance = base_mobile_sale_chance
		if campaign:
			# Campaign can help or hurt, depending on sex preference, mobile optimization and promity to optimal time.
			# Wrong sex match cuts conversion in half. Correct match increases by 25%.
			campaign_sex_preference = campaign["sex_preference"]
			user_sex = users[user_offset][2]
			if campaign_sex_preference == user_sex:
				sale_chance *= 1.25
			else:
				sale_chance *= 0.5

			# If user is on mobile and campaign is not mobile optimized, lose 4/5. Otherwise, quadruple.
			if platform == "mobile":
				if campaign["mobile_optimized"] == True:
					sale_chance *= 4.0
				else:
					sale_chance *= 0.20

			# Increase conversion by up to 50% if we hit the optimal hour. Decay the further we are away.
			hour_delta = abs(campaign["optimal_hour"] - (date_time.hour + date_time.minute / 60.0))
			adjustment = (gaussian(hour_delta, 0, 1) * 0.6 / gaussian(0, 0, 1)) + 0.9
			sale_chance *= adjustment

		if random.random() < sale_chance:
			# If we're on mobile, some chance that we come back up to 8 hours later and buy on desktop.
			if platform == "mobile" and random.random() < chance_switch_mobile_to_desktop:
				platform = "desktop"
				cookie_id = assign_cookie(cookies, user_id, platform)

				# Advance time up to 7 hours. Access the same last product and purchase.
				wait_time = random.uniform(1, 7)
				wait_hours = int(wait_time)
				wait_minutes = int((wait_time % 1) * 60)
				click_time += timedelta(hours=wait_hours, minutes=wait_minutes)
				click = [ click_time, ip_address, product_id, campaign_id, cookie_id, platform, tracking_id ]
				click = [ str(x) for x in click ]
				clicks.append(click)
				num_mobile_switches += 1

			sale = [ click_time, user_id, product_id, campaign_id, cookie_id, tracking_id ]
			sale = [ str(x) for x in sale ]
			sales.append(sale)

	# Persist what we've created.
	sales.sort(key=lambda x: x[0])
	sales_out = GeneratorOutput.factory("fake_sales", child, extras)
	for s in sales:
		sales_out.write('|'.join(s))
	clicks.sort(key=lambda x: x[0])
	clickstream_out = GeneratorOutput.factory("fake_clickstream", child, extras)
	for c in clicks:
		clickstream_out.write('|'.join(c))
	sales_out.close()
	clickstream_out.close()

	print "Number of mobile switches", num_mobile_switches

def gaussian(x, mu, sig):
	return 1./(math.sqrt(2.*math.pi)*sig)*numpy.exp(-numpy.power((x - mu)/sig, 2.)/2)

def assign_cookie(cookies, user_id, platform):
	if user_id not in cookies:
		cookies[user_id] = [ None, None ]
	offset = 0 if platform == "desktop" else 1
	if cookies[user_id][offset] == None:
		cookies[user_id][offset] = uuid.uuid1()
	return cookies[user_id][offset]

def random_ip_address(user_id):
	parts = [ 10, (user_id / (256**2)) % 256, (user_id / 256) % 256, user_id % 256 ]
	return ".".join([ str(x) for x in parts ])

# Example records:
# date,city,state,category,age,sex,promoid,referrerid,zip,ispromo,agegroup
# 2016-03-15^AID^Aclothing^A34^AF^Apromo-01^Arefer-01,12345,Y,26-35
# 2016-03-15^ANY^Acomputers^A33^AM^Apromo-0-2^Arefer-0-2,23456,N,26-35
# Generate 500k records per ID.
def fake_omniture(scale=1, child=0, extras=None):
	if (child >= scale):
		print "Argument mismatch: child too large for scale"
		return 1

	output = open("fake_weblog.%06d.txt" % child, "w")

	random.seed(child)
	zipf_generator = zipf(15, 2.5)

	# Generate data in the week of 2016-03-01 + 7 days * child
	date_min = datetime(2016, 03, 01 + (7 * child), 0, 0)
	date_max = datetime(2016, 03, 01 + (7 * child) + 6, 23, 59)

	# Categories with base weights.
	categories = [
		("accessories", 0.1),
		("automotive", 0.15),
		("books", 0.2),
		("clothing", 0.3),
		("computers", 0.4),
		("electronics", 0.5),
		("games", 0.6),
		("grocery", 0.65),
		("handbags", 0.7),
		("home&garden", 0.75),
		("movies", 0.8),
		("outdoors", 0.85),
		("shoes", 0.95),
		("tools", 1.0)
	]

	# Generate 7 random promos for the week.
	promotions = dict((x, (random.choice(categories)[0], random.uniform(0.03, 0.10))) for x in range(0, 7))

	# Zip code history runs.
	zip_code_history = {}

	# Age grouping.
	age_groups = [ (18, "18-25"), (26, "26-35"), (35, "35-50"), (51, "50+") ]

	for i in xrange(0, 500000):
		date_time = faker.date_time_between(start_date=date_min, end_date=date_max)
		offset = date_time - date_min

		state = faker.state_abbr()

		# "Daily Deal" check.
		promo_id = offset.days
		promotion = promotions[promo_id]
		promo_name = ""
		promo_tag = "{0}-{1}".format(promotion[0], promo_id)
		if random.random() < promotion[1]:
			promo_name = promo_tag
		else:
			promotion = None

		# Referrer ID
		referrer_id = "search"

		# Select a category.
		# If there is a promotion, use its category.
		if promotion != None:
			category = promotion[0]
		else:
			value = random.random()
			fuzz_factor = (random.random() - 0.5) / 30

			i = 0
			prob = categories[i][1] + fuzz_factor
			while prob <= value and i <= len(categories):
				i += 1
				prob = categories[i][1]
			category = categories[i][0]

		# If from a promo, 75% chance of a referring site.
		# Zipfian distribution of referrers within this child bucket.
		# XXX: Need to switch this to a checksum.
		if promotion and random.random() < 0.75:
			# Mix up the offsets a bit based on promo tag.
			shuffle_seed = (sum([ math.sqrt(ord(x)) for x in promo_tag ]) % 99) / 100.0
			ids = range(1, 20)
			random.shuffle(ids, lambda: shuffle_seed)
			referrer_index = zipf_generator.next() - 1
			referrer = ids[referrer_index]
			referrer_id = "{0}-partnerid-{1}".format(promo_tag, referrer)
		elif random.random() < 0.30:
			# Idea here is offsets are shuffled based on category.
			shuffle_seed = (sum([ math.sqrt(ord(x)) for x in category ]) % 99) / 100.0
			ids = range(1, 20)
			random.shuffle(ids, lambda: shuffle_seed)
			referrer_index = zipf_generator.next() - 1
			referrer = ids[referrer_index]
			referrer_id = "partnerid-{0}".format(referrer)

		# Zip code. 70% chance of re-using the old zip code within this category.
		if category not in zip_code_history or random.random() > 0.7:
			zip_code_history[category] = faker.postcode()[0:4] + "0"
		zip_code = zip_code_history[category]

		# Age and sex.
		if category == "handbags":
			if promo_name != "" and random.random() > 0.5:
				age = int(random.gammavariate(5, 1) + 30)
			else:
				age = int(random.gammavariate(5, 4) + 18)
			sex = "M"
			if random.random() < 0.85:
				sex = "F"
		elif category == "accessories" or category == "shoes":
			if promo_name != "" and random.random() > 0.5:
				age = int(random.gammavariate(5, 1) + 30)
			else:
				age = int(random.gammavariate(5, 5) + 18)
			sex = "M"
			if random.random() < 0.75:
				sex = "F"
		elif category == "grocery":
			age = int(random.gammavariate(5, 3) + 18)
			sex = "M"
			if random.random() < 0.5:
				sex = "F"
		elif category == "books":
			age = int(random.gammavariate(5, 2) + 40)
			sex = "M"
			if random.random() < 0.8:
				sex = "F"
		elif category == "games" or category == "electronics":
			if promo_name != "" and random.random() > 0.5:
				age = int(random.gammavariate(5, 1) + 18)
			else:
				age = int(random.gammavariate(5, 2) + 18)
			sex = "M"
			if random.random() < 0.3:
				sex = "F"
		elif category == "computers" or category == "outdoors":
			age = int(random.gammavariate(5, 2) + 18)
			sex = "M"
			if random.random() < 0.3:
				sex = "F"
		elif category == "movies" or category == "clothing":
			if promo_name != "" and random.random() > 0.5:
				age = int(random.gammavariate(5, 1) + 30)
			else:
				age = int(random.gammavariate(5, 4) + 18)
			sex = "M"
			if random.random() < 0.5:
				sex = "F"
		elif category == "home&garden":
			age = int(random.gammavariate(5, 2) + 30)
			sex = "M"
			if random.random() < 0.5:
				sex = "F"
		elif category == "automotive" or category == "tools":
			age = int(random.gammavariate(5, 3) + 18)
			sex = "M"
			if random.random() < 0.10:
				sex = "F"

		is_promo = "0" if promo_name == "" else "1"
		age_group = [ x[1] for x in age_groups if x[0] <= age ][-1]

		record = [ str(date_time).replace(" ", "T"), state, category,
		    str(age), sex, promo_name, referrer_id, zip_code, is_promo, age_group ]
		output.write('|'.join(record) + "\n")

def fake_raw_timeseries(scale=1, child=0):
	nDevices = int(scale*math.log(scale)+1)

	# Always identical generators.
	random.seed(0)
	generators = [ lambda : random.gammavariate(random.randint(8, 12), random.random()) for i in xrange(0, nDevices) ]

	# Change it up.
	random.seed(child)

	table = open("raw_timeseries.%06d.txt" % child, "w")
	ts_step_seconds = 15
	seconds_in_day = 24 * 60 * 60
	tsmin = datetime(2016, 1, child+1, 0, 0)
	start_timestamp = time.mktime(tsmin.timetuple())

	# Generate this day's data.
	for i in xrange(0, seconds_in_day / ts_step_seconds):
		this_time = start_timestamp + i * ts_step_seconds
		for j in xrange(0, nDevices):
			value = round(generators[j](), 3)
			record = [ j, this_time, value ]
			write_rows(table, [record])

def fake_phoenix_timeseries(scale=1, child=0, extras=None):
	num_days = 7 * 8
	record_interval_seconds = 15
	records_per_hour = 3600 / record_interval_seconds
	records_per_file = 24 * records_per_hour * num_days
	num_devices = scale
	total_records = records_per_hour * num_days * 24 * num_devices
	total_files = total_records / records_per_file
	one_block  = records_per_hour * num_devices
	start_rows =  child    * records_per_file
	end_rows   = (child+1) * records_per_file

	if (child >= total_files):
		print "Argument mismatch: child too large for scale"
		return 1

	table = open("timeseries.%06d.txt" % child, "w")
	tsmin = datetime(2016, 1, 1, 0, 0)
	start_timestamp = time.mktime(tsmin.timetuple())

	possible_tags = [ 'AAA', 'BBB', 'CCC', 'DDD', 'EEE' ]

	random.seed(start_rows)
	faker.seed(start_rows)
	num_tags_generator = zipf(4, 5)

	# For random walks.
	walk_values = [ random.random() for i in xrange(start_rows, end_rows) ]
	base_hr = 70
	hr = base_hr
	stock = 100

	for i in xrange(start_rows, end_rows):
		record = []
		hours_in = i / one_block
		block_offset = i - hours_in * one_block
		device_id = block_offset / records_per_hour
		device_offset = block_offset - device_id * records_per_hour
		this_time = start_timestamp + ( hours_in * 60 * 60 ) + device_offset * record_interval_seconds

		record.append(device_id)
		record.append(str(this_time))

		# Move the heart rate, but not too far.
		hr_delta = int( ((walk_values[i-start_rows] - 0.5) / 0.25) ** 3 )
		distance = base_hr - hr
		if abs(distance) > 10:
			hr_delta += distance / abs(distance)
		hr += hr_delta
		record.append("%d" % hr)

		# Temperature random around 20 plus a component for time of day.
		temp = random.normalvariate(20, 0.1)
		offset = random.normalvariate( math.sin(((this_time % 86400) / 86400) * math.pi) * 5, 0.1 )
		record.append("%0.2f" % (temp + offset))

		# Load average (float, between 0 and 10, gamma distribution)
		record.append("%0.2f" % random.gammavariate(9, 0.3))

		# Stock ticker price (float, random walk > 1, step 0.01)
		stock_delta = int( ((walk_values[i-start_rows] - 0.5) / 0.1) ** 3 )
		stock += 0.01 * stock_delta
		if stock < 1:
			stock = 1
		record.append("%0.2f" % stock)

		record.append(faker.boolean())
		tags = []
		num_tags = num_tags_generator.next() - 2
		for j in range(0, num_tags):
			tags.append(random.choice(possible_tags))
		record.append(",".join(tags))
		write_rows(table, [record])

def fake_phoenix(scale=1, child=0, extras=None):
	start_rows = 0
	end_rows = 100
	if (child >= scale):
		print "Argument mismatch: child cannot be greater than scale"
		return 1
	if (scale > 1):
		start_rows = child*1024*100
		end_rows = (child+1)*1024*100

	tbl_alltypes = open("phoenix.%d.txt" % child, "w")
	reseed_split = 100

	for i in xrange(start_rows, end_rows):
		if (i % reseed_split == 0):
			random.seed(i)
			faker.seed(i)
		# PK, integerx8, doublex2, decimalx2, stringx2, booleanx2.
		record = []
		record.append(i)
		record.append(random.randint(-2147483648, 2147483647))
		record.append(random.randint(-147483648, 147483647))
		record.append(random.randint(-47483648, 47483647))
		record.append(random.randint(-7483648, 7483647))
		record.append(random.randint(-483648, 483647))
		record.append(random.randint(-83648, 83647))
		record.append(random.randint(-3648, 3647))
		record.append(random.randint(-648, 647))
		record.append("%0.8f" % random.uniform(-100000, 100000))
		record.append("%0.8f" % random.uniform(-100000, 100000))
		record.append("%0.4f" % random.gammavariate(5, 50))
		record.append("%0.4f" % random.gammavariate(5, 50))
		record.append(faker.paragraph(nb_sentences = random.randint(1, 3)))
		record.append(faker.name())
		record.append(faker.boolean())
		record.append(faker.boolean())
		write_rows(tbl_alltypes, [record])

def fake_allTypes(scale=1, child=0, extras=None):
	start_rows = 0
	end_rows = 100
	if (child >= scale):
		print "Argument mismatch: child cannot be greater than scale"
		return 1
	if (scale > 1):
		start_rows = child*1024*100
		end_rows = (child+1)*1024*100

	tbl_alltypes = open("all_types.%d.txt" % child, "w")
	reseed_split = 100

	for i in xrange(start_rows, end_rows):
		if (i % reseed_split == 0):
			random.seed(i)
			faker.seed(i)
		random_tinyint = random.randint(-128, 127)
		random_smallint = random.randint(-32768, 32767)
		random_int = random.randint(-2147483648, 2147483647)
		random_bigint = random.randint(-9223372036854775808, 9223372036854775807)
		random_float = "%0.4f" % random.uniform(-1000, 1000)
		random_double = "%0.8f" % random.uniform(-100000, 100000)
		random_decimal_18_2 = "%0.2f" % random.gammavariate(5, 50)
		random_decimal_36_6 = "%0.6f" % random.gammavariate(3, 30)
		random_string = faker.paragraph(nb_sentences = random.randint(1, 7))
		random_varchar_5 = faker.zipcode()
		random_varchar_80 = faker.name()
		random_char_2 = faker.state_abbr()
		random_char_11 = faker.ssn()
		random_boolean = faker.boolean()
		random_date = faker.date_time_between(start_date=earliest_date, end_date=latest_date).strftime("%Y-%m-%d")
		random_timestamp = random_date + " 00:00:00"
		record = [ random_tinyint, random_smallint, random_int, random_bigint,
		    random_float, random_double, random_decimal_18_2, random_decimal_36_6,
		    random_string, random_varchar_5, random_varchar_80, random_char_2,
		    random_char_11, random_boolean, random_date, random_timestamp ]
		write_rows(tbl_alltypes, [record])

def usage(generators):
	print "Need -w [{0}]".format(generators)
	print "Usage: generate.py -w workload [-s scale] [-c child] [-k kafka_endpoint]"
	print "Specify Kafka endpoints like: kafka.example.com:9092"
	sys.exit(1)

if __name__ == "__main__":
	workload = None
	generators = " | ".join([ x[5:] for x in locals().keys() if x.startswith("fake_") ])

	try:
		opts, args = getopt(sys.argv[1:], "c:k:s:w:", ['child=', 'scale=', 'workload='])
	except Exception, e:
		print e
		usage(generators)

	scale = 1
	child = 0
	kafka_endpoint = None
	extras = {}
	for (k,v) in opts:
		if k in ['-c','-child']:
			child = int(v)
		elif k in ['-k', '-kafka']:
			kafka_endpoint = v
		elif k in ['-s', '-scale']:
			scale = int(v)
		elif k in ['-w','-workload']:
			workload = v
		else:
			usage(generators)

	if workload == None:
		usage(generators)

	if kafka_endpoint != None:
		import kafka
		producer = kafka.KafkaProducer(bootstrap_servers=kafka_endpoint)
		extras["kafka_producer"] = producer

	workload = "fake_" + workload
	function = locals()[workload]
	ret = function(scale, child, extras)
	sys.exit(ret)
