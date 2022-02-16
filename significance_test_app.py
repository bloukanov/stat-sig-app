from multiprocessing import allow_connection_pickling
import pandas as pd
import numpy as np
from scipy.stats import norm, ttest_ind, ttest_rel, levene
import streamlit as st
from datetime import datetime
import base64

# session_seed = 1

# ---------------------
#   HELPER FUNCTIONS
# ---------------------

# def form_callback():
#     st.session_state.myform = True

# acknowledgers
# ---------------
acknowledgers = ['Ok','Sounds good','Perfect','Great','Alrighty', 'Got it']#, Fantastic 'Excellent',
neg_acknowledgers = ["That's ok", "That's alright", "No problem"]
exclamations = ['!','.']

@st.cache
def generate_acks(m,n,seed):
    np.random.seed(seed)
    acks = []
    neg_acks = []
    for i in range(m):
        acks.append(acknowledgers[np.random.randint(0,len(acknowledgers))] + exclamations[np.random.randint(0,len(exclamations))])
    for i in range(n):
        neg_acks.append(neg_acknowledgers[np.random.randint(0,len(neg_acknowledgers))] + exclamations[np.random.randint(0,len(exclamations))])
    return acks , neg_acks

day_of_year = datetime.now().timetuple().tm_yday
acks = generate_acks(10,10,day_of_year)

# display PDFs
# --------------
def displayPDF(file):
    # Opening file from file path
    with open(file, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')

    # Embedding PDF in HTML
    pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'

    # Displaying File
    st.markdown(pdf_display, unsafe_allow_html=True)


# detect outliers function
# --------------------------
def is_outlier(points, thresh=3.5):
    """
    Returns a boolean array with True if points are outliers and False 
    otherwise.

    Parameters:
    -----------
        points : An numobservations by numdimensions array of observations
        thresh : The modified z-score to use as a threshold. Observations with
            a modified z-score (based on the median absolute deviation) greater
            than this value will be classified as outliers.

    Returns:
    --------
        mask : A numobservations-length boolean array.

    References:
    ----------
        Boris Iglewicz and David Hoaglin (1993), pp. 11-12, "Volume 16: How to Detect and
        Handle Outliers", The ASQC Basic References in Quality Control:
        Statistical Techniques, Edward F. Mykytka, Ph.D., Editor. 
    """
    # if len(points.shape) == 1:
        # points = points[:,None]
    # points = np.array(points)
    median = np.median(points, axis=0)
    # diff = np.sum((points - median)**2, axis=-1)
    diff = (points-median)**2
    diff = np.sqrt(diff)
    med_abs_deviation = np.median(diff)

    modified_z_score = 0.6745 * diff / med_abs_deviation

    return modified_z_score > thresh


# conduct independent samples t-test
# ------------------------------------
def custom_ttest(_group1,_group2,test_type,_0s_desired=None,_0s_included=None,n1=None,n2=None,_is_outlier = is_outlier):

    if test_type == 'ind':

        # check for outliers, not counting 0s.
        # note that if we find outliers and trim them with Yuen's t-test (below), we basically guarantee
        # normality of the test metric. the CLT is only violated if the mean of the distribution
        # of sample means is not defined, which basically only happens when there are signifcant outliers
        # and the distribution has a long tail.
        # we will not include $0 transactions when determining outliers, because all nonzero values may be determined
        # to be outliers, and normality will still hold as long as there are no outliers within the nonzero data.
        outliers1 = sum(_is_outlier(_group1[(_group1 != 0) & (~pd.isna(_group1))]))
        outliers2 = sum(_is_outlier(_group2[(_group2 != 0) & (~pd.isna(_group2))]))

        group1_nona = _group1[~pd.isna(_group1)]
        group2_nona = _group2[~pd.isna(_group2)]

        yes_no_bool = {'Yes':True,'No':False}

        _0s_desired = yes_no_bool[_0s_desired]
        _0s_included = yes_no_bool[_0s_included]

        if (_0s_desired and _0s_included) or not (_0s_desired or _0s_included):
            group1 = group1_nona
            group2 = group2_nona

        elif _0s_desired and not _0s_included:
            group1 = group1_nona.append(pd.Series(np.repeat(0,n1-len(group1_nona))))
            group2 = group2_nona.append(pd.Series(np.repeat(0,n2-len(group2_nona))))

        elif (not _0s_desired) and _0s_included:
            group1 = group1_nona[group1_nona != 0]
            group2 = group2_nona[group2_nona != 0]

        # if there were outliers, set trim value using new group length (if we added 0s)
        if outliers1 > 0 or outliers2 > 0:
            # set trim to the max fraction of outliers between the 2 groups. cannot be >= .5,
            # because the impact of this number of observations will be reduced from each side of the distribution
            trim = round(min(.49,max(outliers1/len(group1),outliers2/len(group2))),6)

            # print(min(_group1[(_group1 != 0) & (~pd.isna(_group1))][_is_outlier(_group1[(_group1 != 0) & (~pd.isna(_group1))])]))        
            # print(min(_group2[(_group2 != 0) & (~pd.isna(_group2))][_is_outlier(_group2[(_group2 != 0) & (~pd.isna(_group2))])]))        

        else:
            trim = 0
        # print(outliers1)
        # print(outliers2)

        # print(trim)

        # check for equality of variance. levene seems to not be sensitive to assumptions of normality.
        var_test = levene(group1,group2)
        # print(var_test[1])
        # if p val is not significant at 10% level, assume variances are equal
        if var_test[1] >= .1:
            result = ttest_ind(group1,group2,equal_var=True,trim=trim)
        # otherwise, can assume they are unequal
        elif var_test[1] < .1:
            result = ttest_ind(group1,group2,equal_var=False,trim=trim)

    elif test_type == 'rel':
            # there should be no NAs in this data
            result = ttest_rel(_group1,_group2)

    # print(len(group1))
    # print(len(group2))
    # print(sum(group1))
    # print(sum(group2))

    pval = result[1]
    mean1 = group1.mean()
    mean2 = group2.mean()
    # if Yuen's trimmed t-test is conducted, let the user know 
    ntrim1 = int(np.floor(trim*len(group1))) # from scipy ttest_ind documentation
    ntrim2 = int(np.floor(trim*len(group2)))
    print(ntrim1)
    trimmed = ntrim1 > 0 or ntrim2 > 0
    if trimmed:
        st.write('''Significant outliers were detected in your data, so we've run a [trimmed t-test] (https://www.real-statistics.com/students-t-distribution/problems-data-t-tests/trimmed-means-t-test).
        This compares the "trimmed means," i.e. the means after removing the outliers, but still includes the outliers for the variance
        calculation. The overall effect is to reduce the impact of the outliers on the significance test.''')
    st.markdown('Mean 1: **{:.4f}**. Mean 2: **{:.4f}**. Mean difference: **{:.4f}**'.format(mean1,mean2,mean1-mean2))
    if trimmed:
        # trimmed means are just the means after removing trimmed values
        sort1  = group1.sort_values()
        sort2 = group2.sort_values()
        
        if ntrim1 == 0:
            tmean1 = mean1
            trimmed_vals1 = pd.Series({1:'None'}).rename('Group 1 trimmed values')
        else:
            tmean1 = sort1[ntrim1:-ntrim1].mean()
            trimmed_vals1 = sort1[:ntrim1].append(sort1[-ntrim1:])
            # make index start with 1 to be user-friendly
            trimmed_vals1.index = np.arange(1,len(trimmed_vals1) + 1)
        if ntrim2 == 0:
            tmean2 = mean2
            trimmed_vals2 = pd.Series({1:'None'}).rename('Group 2 trimmed values')
        else:
            tmean2 = sort2[ntrim2:-ntrim2].mean()
            trimmed_vals2 = sort2[:ntrim2].append(sort2[-ntrim2:])
            # make index start with 1 to be user-friendly
            trimmed_vals2.index = np.arange(1,len(trimmed_vals2) + 1)

        
        st.markdown('Trimmed mean 1: **{:.4f}**. Trimmed mean 2: **{:.4f}**. Trimmed mean difference: **{:.4f}**'.format(tmean1,tmean2,tmean1-tmean2))
    
    st.markdown('**P-Value: '+'{:.3f}**'.format(pval))
    if round(pval,3) <= .010:
        st.success('This difference is significant at the 1% level.')
    elif round(pval,3) <= .050:
        st.success('This difference is significant at the 5% level.')
    elif round(pval,3) <= .100:
        st.success('This difference is significant at the 10% level.')
    elif np.isnan(pval):
        st.error('''Your test result couldn't be calculated. Make sure you have at least 2
        observations in each group!
        ''')
    else:
        st.warning('This difference would not typically be considered statistically significant.')

    if trimmed:
        st.write('''
        You can see the trimmed values below. Note that the same proportion of values must be trimmed from both ends
        of each group. In this case, we trimmed {:.3%} of observations from each end (if this rounds to 0, the group is unaffected).
        '''.format(trim))
        col5, col6 = st.columns(2)
        col5.write(trimmed_vals1.rename('Group 1 trimmed values'))
        col6.write(trimmed_vals2.rename('Group 2 trimmed values'))
        st.write('''
        We've also conducted a [Mann-Whitney U test] (https://en.wikipedia.org/wiki/Mann%E2%80%93Whitney_U_test), a nonparametric
        statistical test that is robust in the presence of outliers. It is sometimes interpreted as a comparison of medians, as opposed
        to means.
        ''')
        # calculate Mann-Whitney statistic and p-value. the statistic represents the number of pairwise comparisons between the two groups
        # the first group wins. the total number of pairwise comparisons is n1*n2. the pval is the chance that the two groups are drawn from the
        # distribution
        from  scipy.stats import mannwhitneyu
        u1, mw_pval = mannwhitneyu(group1,group2)
        n1 = len(group1)
        n2 = len(group2)
        # calculate the 'common language effect size', i.e. the proportion of pairwise comparisons won by the winning group
        u2 = n1*n2 - u1
        cles = max(u1/(n1*n2),u2/(n1*n2))
        # TODO: FORMAT THESE VALUES
        if u1 > u2:
            st.markdown(f'''
            __Items from Group 1 appear to be larger than items from Group 2__. Out of {n1*n2} pairwise comparisons between items of the two groups,
            Group 1 won {u1} ({u1/(u1+u2)}) and Group 2 won {u2} ({u2/(u1+u2)}). Group 1 won {u1-u2} more.
            ''')
        elif u2 > u1:
            st.markdown(f'''
            __Items from Group 2 appear to be larger than items from Group 1__. Out of {n1*n2} pairwise comparisons between items of the two groups,
            Group 2 won {u2} ({u2/(u1+u2)}) and Group 1 won {u1} ({u1/(u1+u2)}). Group 2 won {u2-u1} more.
            ''')

        st.markdown('**P-Value: '+'{:.3f}**'.format(mw_pval))
        if round(mw_pval,3) <= .010:
            st.success('This difference is significant at the 1% level.')
        elif round(mw_pval,3) <= .050:
            st.success('This difference is significant at the 5% level.')
        elif round(mw_pval,3) <= .100:
            st.success('This difference is significant at the 10% level.')
        elif np.isnan(mw_pval):
            # TODO: FIND MINIMUM SAMPLE SIZE
            st.error('''Your test result couldn't be calculated. Make sure you have at least 2
            observations in each group!
            ''')
        else:
            st.warning('This difference would not typically be considered statistically significant.')




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