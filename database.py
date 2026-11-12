import streamlit as st
from neo4j import GraphDatabase


class Neo4jConnection:

    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def query(self, cypher: str, parameters: dict = None):
        with self.driver.session() as session:
            result = session.run(cypher, parameters or {})
            return [record.data() for record in result]


@st.cache_resource
def get_connection(uri, user, password):
    return Neo4jConnection(uri, user, password)


def test_connection(conn: Neo4jConnection) -> bool:
    try:
        result = conn.query("RETURN 1 AS test")
        return len(result) > 0
    except Exception as e:
        st.error(f"Ошибка подключения к Neo4j: {e}")
        return False