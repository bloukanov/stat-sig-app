# from multiprocessing import allow_connection_pickling
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime
from funcs import generate_acks, custom_ttest
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
                        
                    # if means1submit:
                    
                    st.write('''If you'd like to learn more about t-tests or p-values, click below:''')
                    
                    # col6, col7 = st.columns([1,2])
                    # pval_info = col7.button('Learn more about p-values')
                    ttest_info = st.expander('Learn more about t-tests')
                    ttest_info.markdown('''
                    A two-sample __t-test__ is a statistical hypothesis test that helps determine whether there is any real 
                    difference between two sets of data, by comparing their means (averages) and variances.
                    As with any hypothesis test, it proposes a _null hypothesis_ and an _alternative hypothesis_. The null 
                    hypothesis states that the two sets of observations were 
                    drawn from the same distribution, i.e. that there is no real difference between them. If the _p-value_ 
                    produced by the test is low enough, we may reject the null hypothesis and 
                    conclude that there is a real difference between the two groups. 
                    
                    __Be sure to pay attention to which mean is 
                    greater__ -- the test is only concerned with the absolute difference between the two groups, not the
                    direction of the difference.
                    ''') 
                    pval_info = st.expander('Learn more about p-values')
                    pval_info.markdown('''
                    ###### Overview
                    A __p-value__ [(Wikipedia)] (https://en.wikipedia.org/wiki/P-value) is a number between 0 and 1 that is output by statistical 
                    hypothesis tests such as t-tests. 
                    In the case of two-sample t-tests, it represents the probability that the difference in means (averages) observed between
                    two sets of data is due to _random chance_. The larger the difference, and the less variablity there is in the data,
                    the lower the p-value and the more certain we can be that there is a real difference between the two sets.
                    Technically speaking, when the p-value is low enough, we may reject the _null hypothesis_, which states that the 
                    two sets of data are drawn from the same distribution.
                    ###### Thresholds
                    There are various rules of thumb for p-value thresholds. You may notice that in this app, we specifically call out
                    thresholds of .1, .05, and .01 -- these are three very common ones. If  our p-value is less than .01 for example, we may say
                    that we have _99% certainty_ that there is a difference between the two sets of data. Usually, when there is less data
                    we may allow a higher threshold, because smaller sample sizes have more variability. Therefore it is less likely
                    that we will observe a difference even if it exists. (Consider drawing red and blue marbles from a jar, and trying to determine
                    whether the split of red and blue marbles is 50-50. Let's say that after 4 draws, 
                    you hold 3 blue marbles and 1 red. Are you ready to reject the hypothesis? How about if after 400 draws you hold 300 blue and 100 red? 
                    We become more confident after more draws, because of the [law of large numbers] (https://en.wikipedia.org/wiki/Law_of_large_numbers).) 
                    Thus, for data with fewer than 100 observations, a .1 threshold may be sufficient to reject the null hypothesis, whereas for 
                    data with more than 1000, a threshold of .01 would likely be needed.
                    ###### A Word of Caution
                    It is important to interpret the p-value yourself based on your use case, and not just rely on comparison against a threshold.
                    For example, if you have 95 observations and your p-value comes out to .11, wouldn't you agree that there is _some_ significance there?
                    Statistics deals with _probabilities_, so looking to it for black and white answers, while tempting, can also be dangerous because
                    it oversimplifies the reality. Always use your best judgment, and feel free to reach out to the Decision Science team with questions 
                    about how to interpret your results! We are always happy to discuss :).
                    ''')                       
                        

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
        it also produced far less revenue because the CR was far lower. 
        ''')
        st.markdown('''
        That's why sometimes you'll want to evaluate total **Revenue per Visitor (RPV)**. 
        This takes into account both the CR differennces between the groups, and the differences 
        in AG. RPV = CR * AG. In other words, it first asks how many visitors actually gave a gift, 
        and then what was their average gift amount. The way to run a significance test on RPV
        is to add all the visitors to the site who did not give as 0's to the transactions data (I
        can do that for you under 'Evaluate a test'). However, because RPV incorporates variance
        both from CR _and_ from AG, it requires the largest sample size.
        ''')
    elif metric_ready == 'Yes':
        st.write('Under construction!')