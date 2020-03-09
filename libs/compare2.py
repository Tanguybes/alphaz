import  sys, os, re

import pandas as pd
oracle_path = 'C:\oracle\product\instantclient_19_5'

tq_query = ""
with open('tq_query.sql','r') as f:
    tq_query = str(f.read())
    
result = re.findall(r'\[1:.*\]',tq_query)
ke = []
for reg in result:
    k = reg.replace('[1:','').replace(']','')
    ke.append(k)
    
def update_os():
    os.environ["PATH"] = oracle_path + "\;"+os.environ["PATH"]
    #print(os.environ["PATH"])
    #os.environ["NLS_LANG"] = ".UTF8"

    #os.environ['ORACLE_HOME'] = oracle_path
    
import os
update_os()
import cx_Oracle

class Connection():
    conn = None
    dataset  = None
    col_names = []
    
    def __init__(self,host,port,sid,user,pwd):
        dsn_tns         = cx_Oracle.makedsn(host, port, sid)
        self.conn       = cx_Oracle.connect(user,pwd,dsn_tns)
        
    def select(self,query):
        cursor    = self.conn.cursor()
        
        cursor.execute(query)

        col_names = []
        for i in range(0, len(cursor.description)):
            col_names.append(cursor.description[i][0])

        print(col_names)
            
        group = []
        for row in cursor:
            group.append(row)

        dataset = pd.DataFrame(group,columns=col_names)
        
        self.col_names  = col_names
        self.dataset    = dataset
        return dataset

    def get_values(self,key):
        key = key.upper()
        if key in self.col_names:
            return self.dataset[key].values
        return []
        
    def close(self):
        self.conn.close()
        
prod = False
        
if prod:
    rc  = Connection('srv-comisc-db.cro.st.com', '1534', 'comisc','rcadm','Betise_de_Cambrai59')
    tq  = Connection('srv_xt10.cro.st.com', '1531', 'xt10','tqadm','tqadm')
else:
    rc  = Connection('srv-comisc-db-int.cro.st.com', '1531', 'comisc','rcadm','STCrollesDev_38')
    tq  = Connection('crx033.cro.st.com', '1526', 'xt10','tqadm','tqadm')

tq.select("select PHD_ID from PLAGE_HORAIRE_DATES where PHD_DATE_DEBUT > TO_DATE('01/01/2019', 'dd/mm/yyyy')")
tq_shifts = tq.get_values('phd_id')
low, high = tq_shifts[0], tq_shifts[-1]

for el in set(ke):
    seq         = ' %s > %s and %s < %s '%(el, low, el, high)
    tq_query    = tq_query.replace('[1:%s]'%el,seq)

with open('query_output.sql','w') as f:
    f.write(tq_query)

rc.select("select distinct rc_tool_name, rc_area_name from rc_tool where rc_tool_active = 'Y'")

rc_tools = rc.get_values('rc_tool_name')
rc_tools = [x.split('_')[0].replace(' ','') for x in rc_tools]

RC_TOOLS = {}
for i,row in enumerate(rc.dataset.values):
    eqp = row[0].split('_')[0].replace(' ','')
    RC_TOOLS[eqp] = row[1].replace(' ','')

rc.select("select distinct rc_kit_template_name, rc_kit_area from rc_kit_template")
RC_KITS = {}
for i,row in enumerate(rc.dataset.values):
    eqp = row[0].split('_')[0].replace(' ','')
    RC_KITS[eqp] = row[1].replace(' ','')

tq.select("select eq_id, ev_id, ts_kitnummadcs, wa_id from tache_qualite tq where tq.ts_needkit = 1 and tq.ts_valide = 1 and tq.ts_actif = 1")

tq_tools = tq.get_values('eq_id')
tq_kits  = [x.replace('\t','') for x in tq.get_values('ts_kitnummadcs') if x is not None]

print(set(tq_kits))

sep = ';'
output = 'TOOL'+sep+'KIT TEMPLATE'+sep+'EVENT'+sep+'KIT IN RC'+sep+'KIT LINK TO AREA'+sep+'TQ AREA'+sep+'RC AREA\n'

for i,row in enumerate(tq.dataset.values):
    eqp     = row[0].replace(' ','')
    event   = row[1].replace(' ','')
    kit     = row[2] if row[2] is not None else ''
    area    = row[3].replace(' ','')
    area_rc = ''
        
    if eqp in RC_TOOLS:
        area_rc = RC_TOOLS[eqp]
        
    kit_exist   = kit in RC_KITS
    kit_area_ok = False
    if kit_exist:
        kit_area_ok = RC_KITS[kit] == area_rc
        
    print('{:15} {:25} {:20} {:1} {:1} {:10} {:10}'.format(eqp,kit,event,'Y' if kit_exist else 'N','Y' if kit_area_ok else 'N',area,area_rc))
    
    output += sep.join([eqp,kit,event,'Y' if kit_exist else 'N','Y' if kit_area_ok else 'N',area,area_rc]) + '\n'

with open('output.csv','w') as f:
    f.write(output)
exit()

#tq.select("select distinct eq_id from tache_qualite where eq_id in (select distinct eq_id from equipement where eq_actif = 1)")

tq_tools = [x.replace(' ','') for x in tq_tools]

NON_EXISTING_TOOL = list(set(tq_tools) - set(rc_tools))

tq.close()
rc.close()