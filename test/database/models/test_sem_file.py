import random

class TestSemFileQueries:
    def test_simple(self, sample, all_sample_query):
        pass

    def test_rel__sem_analyses(self, sample, all_sample_query):
        for r in all_sample_query:
            files = r.sem_files
            for f in files:
                for a in f.analyses:
                    print(
                        f"{f.id}, {f.default_analysis_id}, {a.id}, {a.mask_url}, {a.px_per_um}, "
                        f"{a.growth_coverage}, {a.automated}"
                    )
        #c = [(fs.id, anr.sem_file_id) for anr, ans in zip (fr.analyses, fs.analyses) for fr, fs in zip(r.sem_files, s.sem_files) for r, s in zip(all_sample_query, sample)]
        #print(c)
   # def test_rel__default_sem_ananlysis
