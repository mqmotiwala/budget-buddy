import streamlit as st
import  utils.css as css

def show_faqs():
    css.divider()
    st.subheader("💡 Frequently Asked Questions")
    sec1, sec2 = st.columns([1, 2]) 
    with sec1:
        css.markdown(f"Have another question? Send me an [{css.highlight("email")}](mailto:mqmotiwala@gmail.com).")

    with sec2:
        with st.expander("What does Budget Buddy do exactly?"):
            answer = """
                Budget Buddy takes care of the heavy lifting with budgeting and expense tracking.
                Just upload your statements and let Budget Buddy handle putting everything together.  
                From there, you can track and review your expenses and get an overview of your finances!
            """
            st.write(answer)

        with st.expander("Is my data secure?"):
            answer = f"""
                Yes, we take security extremely seriously.  

                Budget Buddy is GDPR compliant and uses bank-level 256-bit encryption for your data.
                So, only you can see your data, {css.underline("no one else")}.
            """
            css.markdown(answer)

        with st.expander("What data is collected?"):
            answer = """
                Budget Buddy does not collect any personal information or metadata about you.
                We only collect the data you upload, which is processed to generate insights and reports on your finances.
                
                In addition, you retain full ownership and control.  
                If you ever decide to remove your data, simply submit a deletion request within the app. 
            """
            st.write(answer)
            
        with st.expander("Is there a free tier?"):
            answer = """
            Yes, you can try Budget Buddy for free and you don't even need a credit card!  
            Custom expense categories are excluded from the free tier and you can process only a handful of statements.
            """
            st.write(answer)

        with st.expander("Can I get a refund?"):
            answer = """
                Yes. Just request a refund via email within 7 days of purchase (no questions asked!)
            """
            st.write(answer)

        with st.expander("Can I pay you another way?"):
            answer = f"""
                Sure! You can pay me via 
                [{css.highlight("Venmo")}](https://account.venmo.com/u/mqmotiwala) or 
                [{css.highlight("Paypal")}](https://www.paypal.com/paypalme/mqmotiwala) 
                
                Once done, please [{css.highlight("email")}](mailto:mqmotiwala@gmail.com) about your purchase and I can upgrade you to the paid-tier.  
                Please allow a few hours to get access.

                I have an extensive online presence, so don't worry, I'm not running away with the money. 😊

                [{css.highlight("LinkedIn")}](https://www.linkedin.com/in/mufaddalmotiwala/)
                [{css.highlight("Instagram")}](https://www.instagram.com/m_mufi)
            """
            css.markdown(answer)

    css.empty_space()
