

class TestSemFileQueries:
    def test_simple(self, sample, all_sample_query):
        pass

    def test_rel__sem_analyses(self, sample, all_sample_query):
        for r in all_sample_query:
            files = r.sem_files
            for f in files:
                for a in f.analyses:
                    print(
                        f"{f.id}, {a.sem_file_id}, {a.mask_url}, {a.px_per_um}, {a.growth_coverage}, "
                        f"{a.automated}"
                    )
