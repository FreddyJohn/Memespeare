import logging
import mimetypes
import os
import sqlite3
import boto3
from botocore.exceptions import ClientError
from urllib.parse import unquote, urlparse
import validators
import requests


def connect():
    sqliteConnection = sqlite3.connect('sql.db')
    cursor = sqliteConnection.cursor()
    return cursor, sqliteConnection


def create_db():
    cur, connection = connect()
    table = """ CREATE TABLE IF NOT EXISTS Memes (
                MemeID INTEGER PRIMARY KEY AUTOINCREMENT,
                MemePath TEXT NOT NULL
            ); """
    connection.execute(table)
    table = """ CREATE TABLE IF NOT EXISTS Tags (
                TagID INTEGER PRIMARY KEY AUTOINCREMENT,
                MemeID INT NOT NULL,
                Tag CHAR(255) NOT NULL UNIQUE
            ); """
    connection.execute(table)
    table = """ CREATE TABLE IF NOT EXISTS MemeTags (
               PK INTEGER PRIMARY KEY AUTOINCREMENT,
               MemeID INT NOT NULL,
               TagID INT NOT NULL,
               FOREIGN KEY(MemeID) REFERENCES Memes(MemeID),
               FOREIGN KEY(TagID) REFERENCES Tags(TagID)
    ); """
    connection.execute(table)
    connection.commit()


def wasabi_upload(meme_path):
    s3 = boto3.client('s3', endpoint_url='https://s3.wasabisys.com')
    object_url = os.path.basename(meme_path)
    content_type = mimetypes.guess_type(meme_path)[0]
    meme_path = unquote(urlparse(meme_path).path).replace("/", "", 1)
    print(meme_path, content_type)
    try:
        s3.upload_file(
            meme_path,
            os.getenv("BUCKET_NAME"),
            object_url,
            ExtraArgs={
                "ContentType": content_type})
    except ClientError as e:
        logging.error(e)
        return False
    return object_url, meme_path


def handle_tmp():
    tmp = os.getenv("TEMP_DIR")
    if not os.path.isdir(tmp):
        os.mkdir(tmp)
    os.chdir(tmp)


def download_meme_from_url(image_path):
    handle_tmp()
    r = requests.get(image_path).content
    path = os.path.abspath(os.path.split(image_path)[1])
    with open(path, "wb+") as f:
        f.write(r)
    return path


def insert(meme_path, tags):
    # if meme is an url
    meme_path = meme_path if not validators.url(meme_path) else download_meme_from_url(meme_path)
    # if meme is in the local file system
    object_url, meme_path = wasabi_upload(meme_path)

    cursor, connection = connect()
    if not object_url:
        return
    meme_insert = "INSERT INTO Memes(MemePath) VALUES(?)"
    cursor.execute(meme_insert, (object_url,))
    image_id = cursor.lastrowid
    for tag in tags:
        print(tag)
        try:
            tag_insert = "INSERT INTO Tags(MemeID,Tag) VALUES(?,?)"
            cursor.execute(tag_insert, (image_id, tag))
        except sqlite3.IntegrityError as err:
            bridge_insert = "INSERT INTO MemeTags(MemeID, TagID) VALUES(?,(SELECT TagID From Tags WHERE Tags.Tag =" \
                            "'%s'))" % tag
            cursor.execute(bridge_insert, (image_id,))
            connection.commit()
            logging.error(err)
            return
        tag_id = cursor.lastrowid
        new_bridge_insert = "INSERT INTO MemeTags(MemeID,TagID) VALUES(?,?)"
        cursor.execute(new_bridge_insert, (image_id, tag_id))
        connection.commit()
        print(os.path.isfile(meme_path))
        os.remove(meme_path)


def find_memes(tags):
    cursor, connection = connect()
    meme_collection = []
    print(tags)
    for tag in tags:
        meme_query = "SELECT MemePath FROM Memes JOIN MemeTags ON MemeTags.MemeID = Memes.MemeID JOIN Tags " \
                     "ON Tags.TagID = MemeTags.TagID WHERE Tags.Tag = '%s' " % tag
        cursor.execute(meme_query)
        memes = cursor.fetchall()
        meme_collection.extend([meme[0] for meme in memes])
    return meme_collection


def get_memes_from_wasabi(meme_collection):
    handle_tmp()
    s3 = boto3.client('s3', endpoint_url='https://s3.wasabisys.com')
    for meme in meme_collection:
        print("downloading meme")
        s3.download_file("forthememes", meme, meme)
    return meme_collection
