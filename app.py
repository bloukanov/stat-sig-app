# from multiprocessing import allow_connection_pickling
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime
from funcs import generate_acks, custom_ttest, ttest_pval_dropdowns
from scipy.stats import norm

# session_seed = 1

day_of_year = datetime.now().timetuple().tm_yday
acks = generate_acks(10,10,day_of_year)


#-----------------------------------------------------
#-----------------------------------------------------
# st.write(pd.read_csv('test.csv'))

st.title('Statistical Significance Workbook')
# st.header('Brought to you by the Decision Science team')

st.write('''Hi there! This workbook can help you plan a new test, or determine 
if the results of your recent test were statistically significant. Please use the sidebar to
select which you'd like to do.''')
plan_eval = st.sidebar.selectbox('Plan or Evaluate?',['Select one','Plan a test', 'Evaluate a test'])

# st.write('')
# st.write('To begin, please use the sidebar to choose ')
# st.write('''To begin, please use the sidebar select whether you are testing a difference in rates, such as CTR,
# or a difference in means, such as average gift.''')

if plan_eval == 'Evaluate a test':
    means_rates =  st.sidebar.selectbox('Rates or Means?',['Select one','Difference in rates','Difference in means'])
    st.write(acks[0][0] + ''' Now please select whether you are testing a difference in rates, such as CTR,
    or a difference in means, such as average gift.''')

    if means_rates == 'Difference in rates':
        st.write(acks[0][1] + ''' We'll conduct a [pooled two-proportion z-test] (https://en.wikipedia.org/wiki/Test_statistic#Common_test_statistics). 
        Input the number of positive and total outcomes in each group. 
        For example, for email CTR, this would be clicks and emails received, respectively. Note that the two groups
        must be independent of one another.
        ''')
        with st.form('submit_rate_inputs'):
            col1, col2 = st.columns(2)
            acts1 = col1.number_input('Positive outcomes for Group 1',0)
            acts2 = col2.number_input('Positive outcomes for Group 2',0)
            n1 = col1.number_input('Total outcomes for Group 1',1)
            n2 = col2.number_input('Total outcomes for Group 2',1)

            rates_submit = st.form_submit_button()
            if rates_submit:
                p = (acts1+acts2)/(n1+n2)
                rate1 = acts1/n1
                rate2 = acts2/n2
                pval = 2*norm.cdf(-1*abs((rate1-rate2)/np.sqrt(p*(1-p)*(1/n1+1/n2))))
                # print(pval)
                st.markdown('Rate 1: **{:.4f}**. Rate 2: **{:.4f}**. Rate difference: **{:.4f}**'.format(rate1,rate2,rate1-rate2))
                st.markdown('**P-Value: '+'{:.3f}**'.format(pval))
                # if sample size assumptions are met
                if acts1 >= 5 and acts2 >= 5 and n1-acts1 >= 5 and n2-acts2 >= 5: 
                    if round(pval,3) <= .010:
                        st.success('This difference is significant at the 1% level.')
                    elif round(pval,3) <= .050:
                        st.success('This difference is significant at the 5% level.')
                    elif round(pval,3) <= .100:
                        st.success('This difference is significant at the 10% level.')
                    else:
                        st.warning('This difference would not typically be considered statistically significant.')
                else:
                    if round(pval,3) <= .010:
                        st.warning('''This difference is significant at the 1% level.
                        However, it is recommended that there be at least 5 action and 5 non-action observations
                        in each group. Your data samples do not meet this criterion, so take these results with a grain of salt.
                        ''')
                    elif round(pval,3) <= .050:
                        st.warning('''This difference is significant at the 5% level.
                        However, it is recommended that there be at least 5 action and 5 non-action observations
                        in each group. Your data samples do not meet this criterion, so take these results with a grain of salt.
                        ''')
                    elif round(pval,3) <= .100:
                        st.warning('''This difference is significant at the 10% level.
                        However, it is recommended that there be at least 5 action and 5 non-action observations
                        in each group. Your data samples do not meet this criterion, so take these results with a grain of salt.
                        ''')
                    else:
                        st.warning('''This difference would not typically be considered statistically significant.
                        However, it is recommended that there be at least 5 action and 5 non-action observations
                        in each group. Your data samples do not meet this criterion, so take these results with a grain of salt.
                        ''')                  
                

    elif means_rates == 'Difference in means':
        st.write(acks[0][2] + ''' Are the 2 groups independent of one another? (This will usually be the case,
        unless you are comparing, say, 2 different treatments given to the exact same people.)''')
        ind = st.sidebar.selectbox('Independent samples?', ['Select one','Yes','No'])  
        # print(ind)  
        if ind == 'Yes':
            st.write(acks[0][3] + ''' We'll conduct an [independent samples t-test] (https://en.wikipedia.org/wiki/Student%27s_t-test#Independent_(unpaired)_samples). 
            If you're assessing an ad campaign or website test, would you like to account for recipients or visitors who did not
            make a gift? (If you are not assessing one of these, just select 'No'.) This metric would be total revenue per recipient or visitor, as opposed to average gift.
            You can read more about these metrics under 'Plan a test,' and even more
            [here] (https://vwo.com/blog/important-ecommerce-metrics/) (average order value is the ecommerce
            equivalent of average gift).
            ''')
            rev_per_sess = st.sidebar.selectbox('Consider all recipients or visitors?',['Select one','Yes','No'])
            if rev_per_sess == 'No':
                st.write(acks[0][6] + ''' Upload a csv with your data in columns named 'Group1' and 'Group2,' and click Submit.
                Your data should be at the transaction (not constituent) level, and your evaluation 
                metric will be average gift.
                ''')
                _0s_in_data = 'No'
                total_obs1 = None
                total_obs2 = None
                with st.form('submit mean inputs 0'):
                    upload = st.file_uploader('Upload data', type='csv')
                    means0submit = st.form_submit_button()
                    if means0submit:
                        df = pd.read_csv(upload)
                        custom_ttest(df.Group1,df.Group2,'ind',rev_per_sess,_0s_in_data,n1=total_obs1,n2=total_obs2)
                ttest_pval_dropdowns()
            
            elif rev_per_sess == 'Yes':
                st.write(acks[0][4] + ''' Does your data have 0's to represent recipients or visitors without a transaction?''')
                _0s_in_data = st.sidebar.selectbox('Data for every session or visitor?',['Select one','Yes','No'])

                if _0s_in_data != 'Select one':

                    if _0s_in_data == 'Yes':
                        st.write(acks[0][5] + ''' Upload a csv with your data in columns named 'Group1' and 'Group2,' and click Submit.
                        If your data is at the transaction level, your evaluation metric will be revenue per session. If it is grouped to the constituent
                        level, it will be revenue per constituent.
                        ''')
                        total_obs1 = None
                        total_obs2 = None

                    # elif rev_per_sess == 'No':
                    #     st.write(acks[0][6] + ''' Upload a csv with your data in columns named 'Group1' and 'Group2,' and click Submit.
                    #     Your data should be at the transaction (not constituent) level, and your evaluation 
                    #     metric will be average gift.
                    #     ''')
                    #      _0s_in_data = 'No'
                    #     total_obs1 = None
                    #     total_obs2 = None

                    elif _0s_in_data == 'No':
                        st.write(acks[1][0] + ''' I can adjust that for you. Enter the total number of observations for each group
                        (including those without a transaction), and then upload a csv with your transactions data in columns named 'Group1' and 'Group2.'
                        Then click Submit. If your data is at the transaction level, the number of observations should be the total number of sessions or ad impressions,
                        and your evaluation metric will be revenue per session or impression. If your data is grouped to the constituent level, the total number of observations
                        should be the number of unique constituents who saw the ad (i.e., the ad's reach), and your metric will be revenue per constituent.
                        ''')
                        col3, col4 = st.columns(2)
                        total_obs1 = col3.number_input('Total observations for Group 1',1)
                        total_obs2 = col4.number_input('Total observations for Group 2',1)
                    # elif (rev_per_sess == 'No' and _0s_in_data == 'Yes'):
                    #     st.write(acks[1][1] + ''' I'll remove the 0's for you. Upload a csv with your data in 
                    #     columns named 'Group1' and 'Group2,' and click Submit. Your data should be at the transaction (not constituent) level, and your evaluation 
                    #     metric will be average gift.
                    #     ''')
                    #     total_obs1 = None
                    #     total_obs2 = None

                    with st.form('submit mean inputs 1'):
                        upload = st.file_uploader('Upload data', type='csv')
                        means1submit = st.form_submit_button()
                        if means1submit:
                            df = pd.read_csv(upload)
                            custom_ttest(df.Group1,df.Group2,'ind',rev_per_sess,_0s_in_data,n1=total_obs1,n2=total_obs2)

                    ttest_pval_dropdowns()                    

        elif ind == 'No':
            st.write(acks[0][6] + ''' We'll conduct a [paired samples t-test] (https://en.wikipedia.org/wiki/Student%27s_t-test#Paired_samples).
            Upload a csv with your data in columns named 'Group1' and 'Group2,' and click Submit. 
            Note that both groups must have the same number of observations.
            ''')
            with st.form('submit mean inputs 2'):
                upload = st.file_uploader('Upload data', type='csv')
                means2submit = st.form_submit_button()
                if means2submit:
                    df = pd.read_csv(upload)
                    custom_ttest(df.Group1,df.Group2,'rel')
            
            ttest_pval_dropdowns()

elif plan_eval == 'Plan a test':
    # st.write('Under construction!')
    st.write(acks[0][7] + '''
    Have you decided on a test metric yet?
    ''')
    metric_ready = st.sidebar.selectbox('Metric ready?',['Select one','Yes','No'])
    if metric_ready == 'No':
        st.write(acks[1][2] + '''
        There are several things to consider when choosing the primary metric for your test. 
        ''')
        st.markdown('''
        A rate metric, such as **Conversion Rate (CR)**, will require the smallest sample size 
        and therefore the least test runtime to produce a satisfactory result. 
        ''')
        st.markdown('''If you want to measure a difference in giving behavior, you can use 
        a metric such as **Average Gift (AG)**. This can be misleading, though, so be careful.
        Imagine you have two groups of the same size; Group 1 gave 1,000 $99 gifts, and Group 2 
        gave just 1 $100 gift. A comparison of AG would show that Group 2 performed better, but 
        it also produced far less revenue because the CR was much lower. 
        ''')
        st.markdown('''
        That's why sometimes you'll want to evaluate total **Revenue per Visitor (RPV)**. 
        This takes into account both the CR differennces between the groups, and the differences 
        in AG. RPV = CR * AG. In other words, it first asks how many visitors actually gave a gift, 
        and then what was their average gift amount. The way to run a significance test on RPV
        is to add all the visitors to the site who did not give as 0's to the transactions data (I
        can do that for you under 'Evaluate a test'). However, because RPV incorporates variance
        both from CR _and_ from AG, it requires the largest sample size to get a proper read.
        ''')
    elif metric_ready == 'Yes':
        st.write('Under construction!')