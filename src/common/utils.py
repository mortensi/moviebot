import json
import os
import redis
import numpy as np
import csv

from redis.commands.search.query import Query
from sentence_transformers import SentenceTransformer
from src.common.config import AppConfig
from redis.commands.search.field import TextField, TagField, VectorField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType


def search_by_crew(crew):
    movies = {}

    rs = get_db().ft("movie_idx") \
        .search(Query(f"@crew:({crew})")
                .return_field("names")
                .return_field("$.score")
                .paging(0, 50))

    for movie in rs.docs:
        movies['names'] = movie['$.score']

    movie_info = {
        "movies": movies
    }
    return json.dumps(movie_info)


def moviebot_init():
    print("Checking if Moviebot is installed")
    if (get_db().get("moviebot:status") is None):
        get_db().set("moviebot:status", "installing")
        print("Moviebot is not installed, installing it...")
        create_index()
        load()
        create_embeddings()
        get_db().set("moviebot:status", "installed")
        print("Moviebot is now installed")
    else:
        print("Moviebot is already installed")


# from src.common.utils import *
def load():
    conn = get_db()
    with open(AppConfig.DATA_PATH, encoding='utf-8') as csvf:
        csvReader = csv.DictReader(csvf)
        cnt = 0
        for row in csvReader:
            conn.json().set(f'moviebot:movie:{cnt}', '$', row)
            cnt = cnt + 1


def create_embeddings():
    conn = get_db()
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    for key in get_db().scan_iter(match='moviebot:movie:*'):
        print(f"creating the embedding for {key}")
        result = get_db().json().get(key, "$.names", "$.overview", "$.crew", "$.score", "$.genre")
        movie = f"movie title is: {result['$.names'][0]}\n"
        movie += f"movie genre is: {result['$.genre'][0]}\n"
        movie += f"movie crew is: {result['$.crew'][0]}\n"
        movie += f"movie score is: {result['$.score'][0]}\n"
        movie += f"movie overview is: {result['$.overview'][0]}\n"
        movie += f"movie overview is: {result['$.overview'][0]}\n"
        conn.json().set(key, "$.overview_embedding", get_embedding_list(model, movie))


def vss(model, query):
    context = ""
    prompt = ""
    q = Query("@embedding:[VECTOR_RANGE $radius $vec]=>{$YIELD_DISTANCE_AS: score}") \
        .sort_by("score", asc=True) \
        .return_fields("overview", "names", "score", "$.crew", "$.genre", "$.score") \
        .paging(0, 3) \
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
            # print("the score is: " + str(x['score']))
            movie = f"movie title is: {x['names']}\n"
            movie += f"movie genre is: {x['$.genre']}\n"
            movie += f"movie crew is: {x['$.crew']}\n"
            movie += f"movie score is: {x['$.score']}\n"
            movie += f"movie overview is: {x['overview']}\n"
            context += movie + "\n"

    if len(context) > 0:
        prompt = '''Use the provided information to answer the search query the user has sent.
            The information in the database provides three movies, chose the one or the ones that fit most.
            If you can't answer the user's question, say "Sorry, I am unable to answer the question, try to refine your question". Do not guess. You must deduce the answer exclusively from the information provided. 
            The answer must be formatted in markdown or HTML.
            Do not make things up. Do not add personal opinions. Do not add any disclaimer.

            Search query: 

            {}

            Information in the database: 

            {}
            '''.format(query, context)

    return prompt


def create_index():
    indexes = get_db().execute_command("FT._LIST")
    if "movie_idx" not in indexes:
        index_def = IndexDefinition(prefix=["moviebot:movie:"], index_type=IndexType.JSON)
        schema = (TextField("$.crew", as_name="crew"),
                  TextField("$.overview", as_name="overview"),
                  TagField("$.genre", as_name="genre"),
                  TagField("$.names", as_name="names"),
                  VectorField("$.overview_embedding", "HNSW", {"TYPE": "FLOAT32", "DIM": 384, "DISTANCE_METRIC": "COSINE"}, as_name="embedding"))
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


def store_conversation(question, prompt, response):
    data = {'question': question,
            'prompt': prompt,
            'response': response}
    get_db().xadd("moviebot:conversation", data)


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


