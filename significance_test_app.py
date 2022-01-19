import pandas as pd
import numpy as np
from scipy.stats import norm, ttest_ind, ttest_rel, levene
import streamlit as st

# session_seed = 1

acknowledgers = ['Ok','Sounds good','Perfect','Excellent','Great','Alrighty']#, Fantastic
neg_acknowledgers = ["That's ok", "That's alright", "No problem"]
exclamations = ['!','.']

@st.cache
def generate_acks(m,n):
    # np.random.seed(sesh_seed)
    acks = []
    neg_acks = []
    for i in range(m):
        acks.append(acknowledgers[np.random.randint(0,len(acknowledgers))] + exclamations[np.random.randint(0,2)])
    for i in range(n):
        neg_acks.append(neg_acknowledgers[np.random.randint(0,len(neg_acknowledgers))] + exclamations[np.random.randint(0,2)])
    return acks , neg_acks

acks = generate_acks(10,10)

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
        st.write(acks[0][1] + ''' Input the number of actions taken by each group, and the number of
        opportunities each had to take this action. For example, for email CTR, this would be clicks 
        and emails received, respectively.''')
        with st.form('submit_rate_inputs'):
            col1, col2 = st.columns(2)
            acts1 = col1.number_input('Actions taken by Group 1',0)
            acts2 = col2.number_input('Actions taken by Group 2',0)
            n1 = col1.number_input('Opportunities for Group 1',1)
            n2 = col2.number_input('Opportunities for Group 2',1)

            rates_submit = st.form_submit_button()
            # source: https://www.statisticshowto.com/probability-and-statistics/hypothesis-testing/z-test/#:~:text=This%20tests%20for%20a%20difference,proportions%20are%20not%20the%20same.
            if rates_submit:
                p = (acts1+acts2)/(n1+n2)
                rate1 = acts1/n1
                rate2 = acts2/n2
                pval = 2*norm.cdf(-1*abs((rate1-rate2)/np.sqrt(p*(1-p)*(1/n1+1/n2))))
                st.write('Rate 1: {:.4f}. Rate 2: {:.4f}. Rate difference: {:.4f}'.format(rate1,rate2,rate1-rate2))
                st.write('P-Value: '+'{:.3f}'.format(pval))
                if pval < .01:
                    st.success('This difference is significant at the 1% level.')
                elif pval < .05:
                    st.success('This difference is significant at the 5% level.')
                elif pval < .1:
                    st.success('This difference is significant at the 10% level.')
                else:
                    st.warning('This difference would not typically be considered statistically significant.')

    elif means_rates == 'Difference in means':
        rev_per_sess = st.sidebar.selectbox('Consider all sessions?',['Select one','Yes','No'])
        st.write(acks[0][2] + ''' Would you like to account for emails or sessions that did not
        result in a gift? This metric would be revenue per session, as opposed to average gift.
        INCLUDE LINKS''')
        if rev_per_sess != 'Select one':
            st.write(acks[0][3] + ''' Does your data have 0's to represent sessions without a transaction?''')
            _0s_in_data = st.sidebar.selectbox('Data for every session?',['Select one','Yes','No'])
        if (rev_per_sess == 'Yes' and _0s_in_data == 'Yes') or (rev_per_sess == 'No' and _0s_in_data == 'No'):
            st.write(acks[0][4] + ''' Are the 2 groups independent of one another? This will usually be the case,
            unless you are comparing, say, 2 different treatments given to the exact same people.''')
            ind = st.sidebar.selectbox('Independent samples?', ['Select one','Yes','No'])  
            # print(ind)  
            if ind == 'Yes':
                st.write(acks[0][5] + ''' Upload a csv with your data in columns named 'Group1' and 'Group2.'
                ''')
                with st.form('submit mean inputs 1'):
                    upload = st.file_uploader('Upload data', type='csv')
                    means1submit = st.form_submit_button()
                    if means1submit:
                        df = pd.read_csv(upload)
                        # check for equality of variance. levene seems to not be sensitive to assumptions of normality.
                        var_test = levene(df.Group1[~pd.isna(df.Group1)],df.Group2[~pd.isna(df.Group2)])
                        print(var_test[1])
                        # if p val is not significant at 10% level, assume variances are unequal
                        if var_test[1] > .1:
                            result = ttest_ind(df.Group1,df.Group2,nan_policy='omit',equal_var=False)
                        # otherwise, can assume they are equal
                        else:
                            result = ttest_ind(df.Group1,df.Group2,nan_policy='omit',equal_var=True)
                        pval = result[1]
                        mean1 = df.Group1.mean()
                        mean2 = df.Group2.mean()
                        st.write('Mean 1: {:.2f}. Mean 2: {:.4f}. Mean difference: {:.2f}'.format(mean1,mean2,mean1-mean2))
                        st.write('P-Value: '+'{:.3f}'.format(pval))
                        if pval < .01:
                            st.success('This difference is significant at the 1% level.')
                        elif pval < .05:
                            st.success('This difference is significant at the 5% level.')
                        elif pval < .1:
                            st.success('This difference is significant at the 10% level.')
                        else:
                            st.warning('This difference would not typically be considered statistically significant.')


            # st.write(acks[0][5] + ''' Upload a csv with your data in columns named 'Group1' and 'Group2.'
            # ''')
            # with st.form('submit mean inputs 2'):
            #     st.file_uploader('Upload data', type='csv')
            #     means1submit = st.form_submit_button()
            #     if means1submit:
            #         pass

        elif (rev_per_sess == 'Yes' and _0s_in_data == 'No'):
            st.write('''No problem! I can adjust that for you. Upload a csv with your data in 
            columns named 'Group1' and 'Group2.'
            ''')
        elif (rev_per_sess == 'No' and _0s_in_data == 'Yes'):
            st.write('''No problem! I can adjust that for you. Upload a csv with your data in 
            columns named 'Group1' and 'Group2.'
            ''')