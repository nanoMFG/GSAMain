
class TestAuthorQueries:

    def test_simple(self, sample, all_sample_query):
        pass

    def test__json_encodable(self, sample, all_sample_query):
        for r in all_sample_query:
            for a in r.authors:
                print(a.json_encodable)