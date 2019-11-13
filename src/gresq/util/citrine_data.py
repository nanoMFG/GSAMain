import pandas as pd
from .database import sample, preparation_step

# Check if all values in a frame are null
def check_null(df):
    return df.isnull().all()


def _generate_citrine_to_sample_map():
    """Generate a dictionary mapping db column name to integer 
       position of correspoding column in the CSV """
    cmap = {}
    cmap["material_name"] = 0
    cmap["formula"] = 1
    cmap["identifier"] = 2
    cmap["average_thickness_of_growth"] = 3
    cmap["standard_deviation_of_growth"] = 4
    cmap["number_of_layers"] = 5
    cmap["growth_coverage"] = 6
    cmap["domain_size"] = 7
    cmap["geometry"] = 8
    cmap["silicon_peak_shift"] = 9
    cmap["silicon_peak_amplitude"] = 10
    cmap["silicon_fwhm"] = 11
    cmap["d_peak_shift"] = 12
    cmap["d_peak_amplitude"] = 13
    cmap["d_fwhm"] = 14
    cmap["g_peak_shift"] = 15
    cmap["g_peak_amplitude"] = 16
    cmap["g_fwhm"] = 17
    cmap["g_prime_peak_shift"] = 18
    cmap["g_prime_peak_amplitude"] = 19
    cmap["g_prime_fwhm"] = 20
    cmap["lorenztians_under_g_prime_peak"] = 21
    cmap["sample_surface_area"] = 22
    cmap["thickness"] = 23
    cmap["diameter"] = 24
    cmap["length"] = 25
    cmap["catalyst"] = 26
    cmap["tube_diameter"] = 27
    cmap["cross_sectional_area"] = 28
    cmap["tube_length"] = 29
    cmap["base_pressure"] = 30
    return cmap


def _generate_sample_coltype_map():
    """Generate a dictionary keyed by table column name to lookup the datatype of that column."""

    tmap = {}
    s = sample()
    for c in s.__table__.columns:
        tmap[c.name] = c.type
    return tmap


def _generate_citrine_to_preparation_step_map():
    """Generate a dictionary mapping db column name to integer 
       position of correspoding column in the CSV """

    cmap = {}
    cmap["name"] = 0
    cmap["timestamp"] = 1
    cmap["furnace_temperature"] = 2
    cmap["furnace_pressure"] = 3
    cmap["sample_location"] = 4
    cmap["helium_flow_rate"] = 5
    cmap["helium_flow_rate"] = 6
    cmap["hydrogen_flow_rate"] = 7
    cmap["hydrogen_flow_rate"] = 8
    cmap["carbon_source"] = 9
    cmap["carbon_source_flow_rate"] = 10
    cmap["carbon_source_flow_rate"] = 11
    cmap["argon_flow_rate"] = 12
    cmap["argon_flow_rate"] = 13
    return cmap


def _generate_pstep_coltype_map():
    """Generate a dictionary keyed by table column name to lookup the datatype of that column."""

    tmap = {}
    s = preparation_step()
    for c in s.__table__.columns:
        tmap[c.name] = c.type
    return tmap


def to_mysql(dbtype, vin):
    """Simple type conversion to push numpy types to native python types which are compatable with DB"""

    if "FLOAT" in dbtype.__str__():
        vout = float(vin)
    elif "INTEGER" in dbtype.__str__():
        vout = int(vin)
    else:
        vout = vin
    return vout


class CitrineModel:
    """CitrineModel class refers to a data model of the CSV layout currently used with Citrine. """

    # Current preparation step model
    maxsteps = 6  # No. of steps currently stored in the csv for 1 stage
    nperstep = 13  # No. of columns per 1 step
    AnnealingStart = 32  # Start column for anneling stage
    GrowingStart = 111  # Start column for Growing stage
    CoolingStart = 190  # Start column for Cooling stage

    def __init__(self):
        self.df = pd.DataFrame()
        self.nrows = 0
        self.nanneal = 0
        self.ngrow = 0
        self.ncool = 0
        self.c2smap = _generate_citrine_to_sample_map()
        self.inverted_c2smap = dict([[v, k] for k, v in self.c2smap.items()])
        self.sample_tmap = _generate_sample_coltype_map()
        self.c2psmap = _generate_citrine_to_preparation_step_map()
        self.inverted_c2psmap = dict([[v, k] for k, v in self.c2psmap.items()])
        self.pstep_tmap = _generate_pstep_coltype_map()

    def import_csv(self, row, session):
        """Add a sample fro mthe CSV dataframe"""

        # Check dataframe

        # Create a temporary dataframe containing only not null values
        tmpdf = self.df.iloc[row, list(self.c2smap.values())].dropna()
        ncols = tmpdf.size

        # iterate on keys from tmp table and add them to the sample table
        s = sample()
        for col in tmpdf.keys():
            idx = self.df.columns.get_loc(col)  # Interger position of column key
            # in full CSV table
            dbkey = self.inverted_c2smap[idx]  # Mapped DB column name

            # Get value from the pandas data series and convert to naitive python
            # data type.
            pval = tmpdf.get(col)  # "Pandas" value
            ptype = type(tmpdf.get(col))  # "Pandas" datatype
            print(row, col, dbkey, ptype)
            dbtype = self.sample_tmap[dbkey]  # Database datatype
            value = to_mysql(dbtype, pval)
            # print(row,col,dbkey,ptype,dbtype,'FLOAT' in dbtype.__str__())
            setattr(s, dbkey, value)

        # print(s.identifier)
        session.add(s)

        # Begin preparations step imports
        nanneal = self._check_prepsteps(row, self.AnnealingStart)
        for stepn in range(0, nanneal):
            col_offset = self.AnnealingStart + stepn * self.nperstep
            pstep = preparation_step()
            pstep.sample_id = s.id
            pstep.name = "Annealing"
            # Create a temporary dataframe containing only not null values
            base_vlist = list(self.c2psmap.values())
            vlist = [x + col_offset for x in base_vlist]
            tmpdf = self.df.iloc[row, vlist].dropna()
            try:
                for col in tmpdf.keys():
                    idx = self.df.columns.get_loc(
                        col
                    )  # Interger position of column key
                    # in full CSV table
                    dbkey = self.inverted_c2smap[
                        idx - col_offset
                    ]  # Mapped DB column name

                    # Get value from the pandas data series and convert to naitive python
                    # data type.
                    pval = tmpdf.get(col)  # "Pandas" value
                    ptype = type(tmpdf.get(col))  # "Pandas" datatype
                    # print(row,col,dbkey,ptype)
                    dbtype = self.sample_tmap[dbkey]  # Database datatype
                    value = to_mysql(dbtype, pval)
                    # print(row,col,dbkey,ptype,dbtype,'FLOAT' in dbtype.__str__())
                    setattr(pstep, dbkey, value)
                session.add(pstep)
            except:
                pass

    def get_column_map(self):
        column_map = {}
        for key, value in self.c2smap.items():
            column_map[key] = self.df.columns[value]
        return pd.Series(column_map)

    def show_column_map(self):
        column_map = {}
        for key, value in self.c2smap.items():
            print(key + ' : "' + self.df.columns[value] + '"')
            column_map[key] = self.df.columns[value]

    def _check_prepsteps(self, row, colstart):
        """Check a specified preparation step """
        nsteps = 0
        for ss in range(
            colstart, colstart + self.maxsteps * self.nperstep, self.nperstep
        ):
            se = ss + self.nperstep
            # print(ss,se)
            tmp_df = self.df.iloc[row, ss:se]
            if check_null(tmp_df):
                nsteps += 1
        return nsteps

    def read_csv(self, csv_file):
        """Read a CSV file into Pandas dataframe and do sainity checks"""
        self.df = pd.read_csv(csv_file, sep=",", float_precision=32)

        (nrows, ncols) = self.df.shape
        self.nrows = nrows

        # Discover preparation steps
        self.nanneal = self._check_prepsteps(0, self.AnnealingStart)
        self.ngrow = self._check_prepsteps(0, self.CoolingStart)
        self.ncool = self._check_prepsteps(0, self.CoolingStart)

        print("nanneal:", self.nanneal)
        print("ngrow:", self.ngrow)
        print("ncool:", self.ncool)


cm = CitrineModel()
