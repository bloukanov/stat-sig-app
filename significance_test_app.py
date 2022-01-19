import pandas as pd
import numpy as np
from scipy.stats import norm, ttest_ind, ttest_rel, levene
import streamlit as st

# session_seed = 1

# ---------------------
#   HELPER FUNCTIONS
# ---------------------

# acknowledgers
# ---------------
acknowledgers = ['Ok','Sounds good','Perfect','Great','Alrighty', 'Got it']#, Fantastic 'Excellent',
neg_acknowledgers = ["That's ok", "That's alright", "No problem"]
exclamations = ['!','.']

@st.cache
def generate_acks(m,n):
    # np.random.seed(sesh_seed)
    acks = []
    neg_acks = []
    for i in range(m):
        acks.append(acknowledgers[np.random.randint(0,len(acknowledgers))] + exclamations[np.random.randint(0,len(exclamations))])
    for i in range(n):
        neg_acks.append(neg_acknowledgers[np.random.randint(0,len(neg_acknowledgers))] + exclamations[np.random.randint(0,len(exclamations))])
    return acks , neg_acks

acks = generate_acks(10,10)


# conduct independent samples t-test
# ------------------------------------
def custom_ttest(_group1,_group2,test_type,_0s_desired=None,_0s_included=None,n1=None,n2=None):

    if test_type == 'ind':

        yes_no_bool = {'Yes':True,'No':False}

        _0s_desired = yes_no_bool[_0s_desired]
        _0s_included = yes_no_bool[_0s_included]

        if (_0s_desired and _0s_included) or not (_0s_desired or _0s_included):
            group1 = _group1
            group2 = _group2

        elif _0s_desired and not _0s_included:
            group1 = _group1.append(pd.Series(np.repeat(0,n1-len(_group1))))
            group2 = _group2.append(pd.Series(np.repeat(0,n2-len(_group2))))

        elif (not _0s_desired) and _0s_included:
            group1 = _group1[_group1 != 0]
            group2 = _group2[_group2 != 0]

        # check for equality of variance. levene seems to not be sensitive to assumptions of normality.
        var_test = levene(group1[~pd.isna(group1)],group2[~pd.isna(group2)])
        # print(var_test[1])
        # if p val is not significant at 10% level, assume variances are equal
        if var_test[1] >= .1:
            result = ttest_ind(group1,group2,nan_policy='omit',equal_var=True)
        # otherwise, can assume they are unequal
        elif var_test[1] < .1:
            result = ttest_ind(group1,group2,nan_policy='omit',equal_var=False)

    elif test_type == 'rel':
            group1 = _group1
            group2 = _group2
            result = ttest_rel(group1,group2,nan_policy='omit')

    # print(len(group1))
    # print(len(group2))

    pval = result[1]
    mean1 = group1.mean()
    mean2 = group2.mean()
    st.write('Mean 1: {:.2f}. Mean 2: {:.2f}. Mean difference: {:.2f}'.format(mean1,mean2,mean1-mean2))
    st.write('P-Value: '+'{:.3f}'.format(pval))
    if pval < .01:
        st.success('This difference is significant at the 1% level.')
    elif pval < .05:
        st.success('This difference is significant at the 5% level.')
    elif pval < .1:
        st.success('This difference is significant at the 10% level.')
    else:
        st.warning('This difference would not typically be considered statistically significant.')



#-----------------------------------------------------
#-----------------------------------------------------


st.title('Statistical Significance Workbook')
# st.header('Brought to you by the Decision Science team')

st.write('''Hi there! This workbook can help you plan a new test, or determine 
if the results of your recent test were statistically significant. Please use the sidebar to
select which you'd like to do.''')
plan_eval = st.sidebar.selectbox('Plan or Evaluate?',['Select one','Plan for a test', 'Evaluate a test'])

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
        Input the number of actions taken by each group, and the number of opportunities each had to take this action. 
        For example, for email CTR, this would be clicks and emails received, respectively.''')
        with st.form('submit_rate_inputs'):
            col1, col2 = st.columns(2)
            acts1 = col1.number_input('Actions taken by Group 1',0)
            acts2 = col2.number_input('Actions taken by Group 2',0)
            n1 = col1.number_input('Opportunities for Group 1',1)
            n2 = col2.number_input('Opportunities for Group 2',1)

            rates_submit = st.form_submit_button()
            if rates_submit:
                p = (acts1+acts2)/(n1+n2)
                rate1 = acts1/n1
                rate2 = acts2/n2
                pval = 2*norm.cdf(-1*abs((rate1-rate2)/np.sqrt(p*(1-p)*(1/n1+1/n2))))
                st.write('Rate 1: {:.4f}. Rate 2: {:.4f}. Rate difference: {:.4f}'.format(rate1,rate2,rate1-rate2))
                st.write('P-Value: '+'{:.3f}'.format(pval))
                # if sample size assumptions are met
                if acts1 >= 5 and acts2 >= 5 and n1-acts1 >= 5 and n2-acts2 >= 5: 
                    if pval < .01:
                        st.success('This difference is significant at the 1% level.')
                    elif pval < .05:
                        st.success('This difference is significant at the 5% level.')
                    elif pval < .1:
                        st.success('This difference is significant at the 10% level.')
                    else:
                        st.warning('This difference would not typically be considered statistically significant.')
                else:
                    if pval < .01:
                        st.warning('''This difference is significant at the 1% level.
                        However, it is recommended that there be at least 5 action and 5 non-action observations
                        in each group. Your data samples do not meet this criterion, so take these results with a grain of salt.
                        ''')
                    elif pval < .05:
                        st.warning('''This difference is significant at the 5% level.
                        However, it is recommended that there be at least 5 action and 5 non-action observations
                        in each group. Your data samples do not meet this criterion, so take these results with a grain of salt.
                        ''')
                    elif pval < .1:
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
            Would you like to account for emails or sessions that did not
            result in a gift? This metric would be revenue per visitor or session, as opposed to average gift.
            You can read more about the relationship between conversion rate, average gift, and revenue per visitor [here] (https://vwo.com/blog/important-ecommerce-metrics/).
            ''')
            rev_per_sess = st.sidebar.selectbox('Consider all sessions?',['Select one','Yes','No'])
            if rev_per_sess != 'Select one':
                st.write(acks[0][4] + ''' Does your data have 0's to represent sessions without a transaction?''')
                _0s_in_data = st.sidebar.selectbox('Data for every session?',['Select one','Yes','No'])

                if _0s_in_data != 'Select one':

                    if (rev_per_sess == 'Yes' and _0s_in_data == 'Yes') or (rev_per_sess == 'No' and _0s_in_data == 'No'):
                        st.write(acks[0][5] + ''' Upload a csv with your data in columns named 'Group1' and 'Group2,' and click Submit.
                        ''')
                        total_obs1 = None
                        total_obs2 = None

                    elif (rev_per_sess == 'Yes' and _0s_in_data == 'No'):
                        st.write(acks[1][0] + ''' I can adjust that for you. Enter the total number of observations for each group
                        (including those without a transaction), and then upload a csv with your data in columns named 'Group1' and 'Group2.'
                        Then click Submit.
                        ''')
                        col3, col4 = st.columns(2)
                        total_obs1 = col3.number_input('Total observations for Group 1',1)
                        total_obs2 = col4.number_input('Total observations for Group 2',1)
                    elif (rev_per_sess == 'No' and _0s_in_data == 'Yes'):
                        st.write(acks[1][1] + ''' I'll remove the 0's for you. Upload a csv with your data in 
                        columns named 'Group1' and 'Group2,' and click Submit.
                        ''')
                        total_obs1 = None
                        total_obs2 = None

                    with st.form('submit mean inputs 1'):
                        upload = st.file_uploader('Upload data', type='csv')
                        means1submit = st.form_submit_button()
                        if means1submit:
                            df = pd.read_csv(upload)
                            custom_ttest(df.Group1,df.Group2,'ind',rev_per_sess,_0s_in_data,n1=total_obs1,n2=total_obs2)
                        
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

elif plan_eval == 'Plan for a test':
    st.write('Under construction!')
