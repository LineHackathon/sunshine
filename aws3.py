#!/usr/bin/python
# -*- coding: utf-8 -*-

import boto3

AWS_S3_BUCKET_NAME = 'checkunreceipt'

def get_db(name):
	#print('get_db')
	s3 = boto3.resource('s3')

	bucket = s3.Bucket(AWS_S3_BUCKET_NAME)

	file_path = 'db' + '/' + name + '.json'
	key = file_path

	for obj in bucket.objects.all():
		print('key:' + obj.key)
		if obj.key.startswith(key):
			#print('hit')
			res = obj.get()
			body = res['Body'].read()
			with open(file_path, 'wb') as fd:
				print(file_path)
				fd.write(body)
				fd.close()
			return file_path

	with open(file_path, 'wb') as fd:
		print('create:' + file_path)
		#fd.write(body)
		fd.close()
		data = open(file_path, 'rb')
		bucket.put_object(Key=key, Body=data)

	return file_path

def update_db(name):
	s3 = boto3.resource('s3')

	bucket = s3.Bucket(AWS_S3_BUCKET_NAME)

	file_path = 'db' + '/' + name + '.json'
	key = file_path
	data = open(file_path, 'rb')
	bucket.put_object(Key=key, Body=data)

#set /static/file_name to S3
#key=gid/file_name
#file_name:receipt_uid_date_time.jpg
def set_receipt(gid, uid, file_name):
	s3 = boto3.resource('s3')

	bucket = s3.Bucket(AWS_S3_BUCKET_NAME)
	print(bucket.name)
	print(bucket.objects.all())
	for obj_summary in bucket.objects.all():
		print(obj_summary)
	# Upload a new file
	file_path = 'static' + '/' + file_name
	key = gid + '/' + uid + '_' + file_name
	data = open(file_path, 'rb')
	bucket.put_object(Key=key, Body=data)
	

#get file and save to /static/file_name
def get_receipt(gid, uid, file_name):
	s3 = boto3.resource('s3')

	bucket = s3.Bucket(AWS_S3_BUCKET_NAME)
	print(bucket.name)
	print(bucket.objects.all())
	for obj_summary in bucket.objects.all():
		print(obj_summary)

	file_path = 'static' + '/' + file_name
	key = gid + '/' + uid + '_' + file_name
	obj = bucket.Object(key)
	res = obj.get()
	body = res['Body'].read()

	with open(file_path, 'wb') as fd:
		print(file_path)
		fd.write(body)
		fd.close()

def delete_receipt(gid, uid, file_name):
	s3 = boto3.resource('s3')

	bucket = s3.Bucket(AWS_S3_BUCKET_NAME)
	print(bucket.name)
	print(bucket.objects.all())
	for obj_summary in bucket.objects.all():
		print(obj_summary)

	file_path = 'static' + '/' + file_name
	key = gid + '/' + uid + '_' + file_name
	obj = bucket.Object(key)
	obj.delete()


if __name__ == "__main__":
	pass