from typing import Union


class Database:
    # queries database using key-values assignments and returns list of results
    def query(self, query: {str: Union[str,int,float]}) -> [object]:
        raise NotImplementedError('Database has to implement the query method.')