class TestRamanSpectrumQueries:
    def test_simple(self, sample, all_sample_query):
        for r in all_sample_query:
            ra = r.raman_analysis
            print(ra)
            #for rs in ra.raman_spectra:
            #    #print(f"{rs.id}, {rs.raman_file_id}, {rs.xcoord}")
            #    print(rs.raman_file)