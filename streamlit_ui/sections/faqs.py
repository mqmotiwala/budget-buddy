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
            answer = """
                Yes. Budget Buddy is GDPR compliant.  
                Your private data is encrypted at all times, and decryption only happens client-side.
                In laymen's terms, **only you** can see your data, no one else.

                Additionally, you are always in control of your data and can request a full deletion at any time from the app. 
            """
            st.write(answer)
            
        with st.expander("Is there a free trial?"):
            answer = """
            Yes, you can try Budget Buddy for free and you don't even need a credit card!  
            Custom expense categories are excluded from the free trial and you're limited to only a handful of statements.
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
