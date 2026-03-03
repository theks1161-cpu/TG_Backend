import resend
import base64
import os

async def send_enquiry_email(data):
    """
    Send enquiry details to admin via Resend API
    """

    email_body = f"""
    New Enquiry Received

    Full Name          : {data.full_name}
    Email Address      : {data.email_address}
    Contact Number     : {data.contact_number}

    Category           : {data.category}
    Destination        : {data.destination}
    
    Additional Dest.   : {data.additional_destination or "N/A"}

    Travel Start Date  : {data.start_date}

    Adults             : {data.adults}
    Children           : {data.children}

    Departure City     : {data.departure_city}

    Referral Source    : {data.referral_source}
    

    Special Requests   : {data.special_requests or "None"}
    """

    email = {
        "from": "Tirth Ghumo <no-reply@tirthghumo.in>",
        "to": ["ceo.tirthghumo@gmail.com"],
        "subject": "New Travel Enquiry Received",
        "text": email_body.strip(),
    }

    try:
        resend.Emails.send(email)
        return {"status": "Enquiry email sent successfully"}
    except Exception as e:
        raise Exception(f"Enquiry email sending failed: {str(e)}")


async def send_enquiry_popup_mail(data):
    """
    Send enquiry popup details to admin via Resend API
    """

    email_body = f"""
    New Enquiry Popup Received

    Full Name         : {data.full_name}
    Contact Number    : {data.contact_number}
    Destination       : {data.destination}
    """

    email = {
        "from": "Tirth Ghumo <no-reply@tirthghumo.in>",
        "to": ["hr.tirthghumo@gmail.com"],
        "subject": "New Enquiry Popup Received",
        "text": email_body.strip(), 
    }

    try:
        resend.Emails.send(email)
        return {"status": "Enquiry popup email sent successfully"}
    except Exception as e:
        raise Exception(f"Enquiry popup email sending failed: {str(e)}")