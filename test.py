from html.parser import HTMLParser
import urllib.request as urllib2
from collections import defaultdict
from datetime import datetime
import sys
import logging
import click
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

@click.command()
@click.option('--url', prompt='url',
              help='URL to analyse')
@click.option('--log/--no-log', default=True, help='Is log to file?', show_default=True)
@click.option('--upload/--no-upload', default=False, help='Is upload log to s3? work only with --log',  show_default=True)
def main(url, log, upload): 
    countTags(url, log, upload)

def countTags(url, log, upload):
    logger = logging.getLogger('tagsLogger')
    file_name='test.log'
    
    logConfigure(logger, log, file_name)

    occurrences = defaultdict(int)

    class MyHtmlParser(HTMLParser):
        def handle_starttag(self, tag, attrs):
            occurrences[tag] += 1

    try:
        html_page = urllib2.urlopen(url)
    except Exception as e:
        if hasattr(e, 'message'):
            print(e.message)
        else:
            print(e)
        return
    
    myParser = MyHtmlParser()
    myParser.feed(str(html_page.read()))
    curDate = datetime.strftime(datetime.now(), '%Y/%m/%d %H:%M')

    logger.info('%s %s %s', url ,  sum(occurrences.values()) ,  dict(occurrences))
    if (log and upload):
        uploadToS3(file_name, 'pythoniossanewnew', file_name+'_test')

def logConfigure(logger, log, file_name):
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s  %(message)s', '%Y/%m/%d %H:%M')
    if(log): 
        fh = logging.FileHandler(file_name)
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

def uploadToS3(file_name, bucket_name, object_name):
    s3 = boto3.resource('s3')
    s3_client = boto3.client('s3')
    location = {'LocationConstraint': 'us-east-2'}
    exists = True
    try:
        s3.meta.client.head_bucket(Bucket=bucket_name)
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            exists = False
    if(exists == False):
        try:
            s3_client.create_bucket(Bucket=bucket_name, CreateBucketConfiguration=location)
        except ClientError as e:
            print(e)
            print("Not uploaded to s3, can't create bucket")
            return

    try:
        response = s3_client.upload_file(file_name, bucket_name, object_name)
    except ClientError as e:
        print(e)
        print("Not uploaded to s3")
        return
    
    print("Uploaded to s3")

if __name__ == '__main__':
   main()
