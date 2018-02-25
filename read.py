import pandas as pd
import gdxpds
import numpy as np
#import gdx2py
#from datetime import datetime

solution_file = 'solution.gdx'
mps_file = 'ReEDSpre.mps'
mps_ls = []
columns = False
with open(mps_file) as mpsfile:
    for line in mpsfile:
        if columns:
            if line[:3] == 'RHS':
                break
            ls = line.split()
            var_ls = ls[0].split('(')
            if len(var_ls) == 1:
                var_ls.append('')
            else:
                var_ls[1] = var_ls[1][:-1].replace('"','')
            con_ls = ls[1].split('(')
            if len(con_ls) == 1:
                con_ls.append('')
            else:
                con_ls[1] = con_ls[1][:-1].replace('"','')
            mps_ls.append(var_ls + con_ls + [float(ls[2])])
        if line[:7] == 'COLUMNS':
            columns = True
df_mps = pd.DataFrame(mps_ls)
df_mps.columns = ['var_name','var_set','con_name','con_set', 'coeff']
#make obj its own column
df_obj = df_mps[df_mps['con_name']=='obj'].copy()
df_obj = df_obj[['var_name','var_set','coeff']]
df_obj = df_obj.rename(columns={'coeff': 'obj'})
df_mps = pd.merge(left=df_mps, right=df_obj, how='left', on=['var_name', 'var_set'], sort=False)


def get_df_symbols(dfs, symbols):
    df_syms = []
    for sym_name in symbols:
        # df_sym = pd.DataFrame(gdx2py.par2list(solution_file, sym_name))
        # df_sym = gdxpds.to_dataframe(solution_file, sym_name, old_interface=False)
        if sym_name not in dfs:
            continue
        df_sym = dfs[sym_name]
        df_sym['sym_name'] = sym_name
        #concatenate all the set columns into one column
        level_col = df_sym.columns.get_loc('Level')
        df_sym['sym_set'] = ''
        for s in range(level_col):
            df_sym['sym_set'] = df_sym['sym_set'] + df_sym.iloc[:,s]
            if s < level_col - 1:
                df_sym['sym_set'] = df_sym['sym_set'] + '.'
        #remove set columns
        df_sym = df_sym.iloc[:,level_col:]
        #remove lower upper scale
        df_sym = df_sym.drop(['Lower', 'Upper', 'Scale'], axis=1)
        df_syms.append(df_sym)
    df_syms = pd.concat(df_syms).reset_index(drop=True)
    return df_syms

dfs = gdxpds.to_dataframes(solution_file)
df_vars = get_df_symbols(dfs, df_mps['var_name'].unique())
df_vars = df_vars.rename(columns={"Level": "var_level", "Marginal": "var_marginal", 'sym_name':'var_name', 'sym_set': 'var_set'})
df = pd.merge(left=df_mps, right=df_vars, how='left', on=['var_name', 'var_set'], sort=False)
df_cons = get_df_symbols(dfs, df_mps['con_name'].unique())
df_cons = df_cons.rename(columns={"Level": "con_level", "Marginal": "con_marginal", 'sym_name':'con_name', 'sym_set': 'con_set'})
df = pd.merge(left=df, right=df_cons, how='left', on=['con_name', 'con_set'], sort=False)
df.loc[df['con_name']=='obj','con_marginal'] = -1
df['component'] = df['coeff']*df['con_marginal']
df['var_lev_and_marg'] = 'normal'
df.loc[(df['var_level'] != 0) & (df['var_marginal'] != 0), 'var_lev_and_marg'] = 'both non-zero'
df.loc[(df['var_level'] == 0) & (df['var_marginal'] == 0), 'var_lev_and_marg'] = 'both zero'
df['profitability'] = np.NaN
df.loc[(df['con_name'] != 'obj') & (pd.notnull(df['obj'])), 'profitability'] = df['component'] / df['obj']
df.to_csv('df.csv',index=False)
import pdb; pdb.set_trace()



# dfs = gdxpds.to_dataframes('ReEDS_model_2024_p.gdx')
# df_sym = gdxpds.to_dataframe('reeds_out_p.gdx', 'AC_loss', old_interface=False)
# df_equ = gdxpds.to_dataframe('reeds_out_p.gdx', 'AC_LOSSES', old_interface=False)
