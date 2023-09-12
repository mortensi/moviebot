import os
import redis
import numpy as np
import csv

from redis.commands.search.query import Query
from sentence_transformers import SentenceTransformer
from config import AppConfig
from redis.commands.search.field import TextField, TagField, VectorField, NumericField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType


# from src.common.utils import *
def load():
    with open(AppConfig.DATA_PATH, encoding='utf-8') as csvf:
        csvReader = csv.DictReader(csvf)
        cnt = 0
        for row in csvReader:
            get_db().json().set(f'movie:{cnt}', '$', row)
            cnt = cnt + 1


def create_embeddings():
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    for key in get_db().scan_iter(match='movie:*'):
        result = get_db().json().get(key, "$.names", "$.overview")
        content = result['$.names'][0] + ". " + result['$.overview'][0]
        get_db().json().set(key, "$.overview_embedding", get_embedding_list(model, content))


def vss(model, query):
    context = ""
    q = Query("@embedding:[VECTOR_RANGE $radius $vec]=>{$YIELD_DISTANCE_AS: score}") \
        .sort_by("score", asc=True) \
        .return_fields("overview", "names", "score") \
        .paging(0, 1) \
        .dialect(2)

    # Find all vectors within VSS_MINIMUM_SCORE of the query vector
    query_params = {
        "radius": AppConfig.VSS_MINIMUM_SCORE,
        "vec": get_embedding_blob(model, query)
    }

    res = get_db().ft("movie_idx").search(q, query_params)

    if (res is not None) and len(res.docs):
        it = iter(res.docs[0:])
        for x in it:
            print("the score is: " + str(x['score']))
            context = context + str(x['names']) + ". " + str(x['overview'])

    return context


def create_index():
    indexes = get_db().execute_command("FT._LIST")
    if "movie_idx" not in indexes:
        index_def = IndexDefinition(prefix=["movie:"], index_type=IndexType.JSON)
        schema = (TextField("$.crew", as_name="crew"),
                  TextField("$.overview", as_name="overview"),
                  TagField("$.genre", as_name="genre"),
                  TagField("$.names", as_name="names"),
                  VectorField("$.overview_embedding", "HNSW", {"TYPE": "FLOAT32", "DIM": 384, "DISTANCE_METRIC": "L2"}, as_name="embedding"))
        get_db().ft('movie_idx').create_index(schema, definition=index_def)
        print("The index has been created")
    else:
        print("The index exists")


def get_embedding_list(model, text):
    embedding = model.encode(text).astype(np.float32).tolist()
    return embedding


def get_embedding_blob(model, text):
    embedding = model.encode(text).astype(np.float32).tobytes()
    return embedding


def get_db(decode=True):
    try:
        return redis.StrictRedis(host=os.getenv('DB_SERVICE', '127.0.0.1'),
                                 port=int(os.getenv('DB_PORT', 6379)),
                                 password=os.getenv('DB_PWD', ''),
                                 db=0,
                                 ssl=os.getenv('DB_SSL', False),
                                 ssl_keyfile=os.getenv('DB_SSL_KEYFILE', ''),
                                 ssl_certfile=os.getenv('DB_SSL_CERTFILE', ''),
                                 ssl_ca_certs=os.getenv('DB_CA_CERTS', ''),
                                 ssl_cert_reqs=os.getenv('DB_CERT_REQS', ''),
                                 decode_responses=decode)
    except redis.exceptions.ConnectionError:
        print("Error getting a Redis connection")


