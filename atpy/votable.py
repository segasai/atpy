from basetable import BaseTable, BaseTableSet

from vo.table import parse
from vo.tree import VOTableFile, Resource, Table, Field

import numpy as np

# Define type conversion dictionary
type_dict = {}
type_dict[np.uint8] = "int"
type_dict[np.int16] = "int"
type_dict[np.int32] = "int"
type_dict[np.int64] = "int"
type_dict[np.float32] = "float"
type_dict[np.float64] = "double"
type_dict[np.str] = "char"
type_dict[np.string_] = "char"
type_dict[str] = "char"

def _list_tables(filename):
    votable = parse(filename)
    tables = {}
    for i,table in enumerate(votable.iter_tables()):
        tables[i] = table.name
    return tables

class VOTable(BaseTable):
    
    "A class for writing vo tables."

    def read(self,filename,echo=False,tid=-1):
                
        self.reset()
        
        # If no table is requested, check that there is only one table
        if tid==-1:
            tables = _list_tables(filename)
            if len(tables) == 1:
                tid = 0
            else:
                print "-"*56
                print " There is more than one table in the requested file"
                print " Please specify the table desired with the tid= argument"
                print " The available tables are:"
                print ""
                for tid in tables:
                    print " tid=%i : %s" % (tid,tables[tid])
                print "-"*56
                return
        
        votable = parse(filename)
        for id,table in enumerate(votable.iter_tables()):
            if id==tid:
                break
                        
        self.table_name = table.ID or table.name
                
        for field in table.fields:
            self.add_column((field.name,table.array[field.name]))
    
    def to_table(self,VOTable):

        table = Table(VOTable)

        # Define some fields
        
        n_rows = len(self.array[self.names[0]])

        fields = []
        for i,name in enumerate(self.names):

            data = self.array[name]
            unit = self.units[name]

            coltype = type(data)

            elemtype=type(data[0])
            arraysize = None
            
            if elemtype==np.ndarray:
                elemtype=type(data[0][0])
                arraysize = str(len(data[0]))
                
            if type_dict.has_key(elemtype):
                datatype = type_dict[elemtype]
            else:
                raise Exception("cannot use numpy type "+str(elemtype))

            if arraysize:
                fields.append(Field(VOTable,ID="col"+str(i),name=name,datatype=datatype,unit=unit,arraysize=arraysize))
            else:
                fields.append(Field(VOTable,ID="col"+str(i),name=name,datatype=datatype,unit=unit))
                
        table.fields.extend(fields)

        table.create_arrays(n_rows)

        for name in self.names:
            table.array[name] = self.array[name]

        table.name = self.table_name

        return table
    
    def write(self,filename,votype='ascii'):

        VOTable = VOTableFile()
        resource = Resource()
        VOTable.resources.append(resource)

        resource.tables.append(self.to_table(VOTable))

        if votype is 'binary':
            VOTable.get_first_table().format = 'binary'
            VOTable.set_all_tables_format('binary')
            
        VOTable.to_xml(filename)
            
        
class VOTableSet(BaseTableSet):
    """ A class for reading and writing a set of VO tables."""

    def __init__(self,tables=None):

        self.tables = []

        if tables:
            if type(tables) == list:
                self.tables = tables
            elif isinstance(tables,BaseTableSet):
                for table in tables.tables:
                    self.tables.append(VOTable(table))
            else:
                raise Exception("Unknown type: "+type(tables))

    def read(self,filename):
        tids = _list_tables(filename)
        self.tables = []
        for tid in tids:
            t = VOTable()
            t.read(filename,tid=tid)
            self.tables.append(t)
          
    def write(self,filename,votype='ascii'):
        
        VOTable = VOTableFile()
        resource = Resource()
        VOTable.resources.append(resource)
        
        for table in self.tables:
            resource.tables.append(table.to_table(VOTable))
        
        if votype is 'binary':
            VOTable.get_first_table().format = 'binary'
            VOTable.set_all_tables_format('binary')

        VOTable.to_xml(filename)