import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import wasserstein_distance as wdist
import warnings
warnings.filterwarnings("ignore")


def create_lmp_vector(web):
    df = pd.read_csv(web, index_col='date')
    df.columns.name = 'time'
    df_stack = df.stack().rename('lmp').reset_index()
    df_stack.index = pd.to_datetime(df_stack['date'] + ' ' + df_stack['time'])
    return df_stack['lmp']


def create_abnormal_index(df, date_range):
    df_target = df[df.index.isin(date_range)]
    df_history = df[~df.index.isin(date_range)]
    all_months = df_target.index.month.unique().values
    abnormal_index = {}
    for month in all_months:
        month_lmps = df_target[df_target.index.month == month]
        history_month_lmps = df_history[df_history.index.month == month]
        for idx in month_lmps.index:
            lmp = month_lmps.loc[idx]
            quantile = np.sum(history_month_lmps < lmp) / len(history_month_lmps)
            abnormal_index[idx] = np.abs(2 * quantile - 1)
    output = pd.Series(abnormal_index)
    return output


def plot_abnormal_index(df, time_label):
    df_ma = df.rolling(7*24).mean()

    fig = plt.figure(figsize=(10, 4))
    ax = fig.add_axes([0.08, 0.22, 0.9, 0.77])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_ylabel('Abnormal Index Value')
    ax.set_xlabel('Date')

    index = df.index
    ax.plot(index, df, c='grey', alpha=0.4, label='Abnormal Index')
    ax.plot(index, df_ma, lw=2.5, label='Weekly Moving Average of Abnormal Index')
    if time_label is not None:
        for d in time_label:
            ax.axvline(x=d, color='#773456', linestyle='--', linewidth=2)

    plt.xticks(index[::96], index[::96].strftime('%m-%d'), rotation=40)
    plt.legend(framealpha=0)
    plt.show()


def calculate_lmp_deviation(df, date_range, months):
    df_target = df[df.index.isin(date_range)]
    all_months = df_target.index.month.unique().values
    df_history = df[~df.index.isin(date_range)]
    df_history = df_history[df_history.index.month.isin(all_months)]
    dist = wdist(df_target, df_history)
    print('LMP Deviation Distance = %.3f' % dist)


def get_covid_case_data(web, date):
    df = pd.read_csv(web, index_col='date')
    df.index = pd.to_datetime(df.index)
    accum_confirm = df.loc[date, 'accum_confirm']
    infect_rate = df.loc[date, 'infect_rate']
    print('Total Confirmed Cases Number = %d' % accum_confirm)
    print('Total Infection Rate = %.3f' % infect_rate)
    return accum_confirm, infect_rate


if __name__ == '__main__':
    # ----- 01. plot abnormal index trend -----
    web_root = 'https://raw.githubusercontent.com/tamu-engineering-research/COVID-EMDA/master/'
    web_target = 'data_release/isone/isone_rto_lmp.csv'
    all_lmps = create_lmp_vector(web_root + web_target)
    state_of_emergence_label = [
        pd.datetime(2020, 3, 9),   # Rhode Island
        pd.datetime(2020, 3, 10),  # Massachusetts, Connecticut
        pd.datetime(2020, 3, 13),  # Maine, Vermont, New Hampshire
    ]

    abnormal_index = create_abnormal_index(
        df=all_lmps,
        date_range=pd.date_range(pd.datetime(2020, 2, 1), pd.datetime(2020, 5, 31), freq='H'),
    )
    plot_abnormal_index(abnormal_index, state_of_emergence_label)

    # ----- 02. calculate lmp deviation -----
    web_root = 'https://raw.githubusercontent.com/tamu-engineering-research/COVID-EMDA/master/'
    webs = {
        mkt: (web_root + 'data_release/' + mkt + '/' + mkt + '_rto_lmp.csv',
              web_root + 'data_release/' + mkt + '/' + mkt + '_rto_covid.csv')
        for mkt in ['caiso', 'miso', 'isone', 'nyiso', 'pjm', 'spp', 'ercot']
    }

    for mkt, (web1, web2) in webs.items():
        print('Market = %s' % mkt)
        calculate_lmp_deviation(
            df=create_lmp_vector(web1),
            date_range=pd.date_range(pd.datetime(2020, 3, 1), pd.datetime(2020, 5, 31), freq='H'),
            months=[3, 4, 5],
        )
        get_covid_case_data(web2, pd.datetime(2020, 5, 31))
        print('')

