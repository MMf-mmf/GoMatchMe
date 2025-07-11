from ..models import BountyOrder



def create_bounty_order(from_user, to_user, amount, email, address, zip, city, recurring_payment, expiration_date, number_of_months, bounty_order_id=None):
    try:
        bounty_order, created = BountyOrder.objects.update_or_create(
            id=bounty_order_id, # look up value
            defaults={ # values to update or create
                'from_user': from_user,
                'to_user': to_user,
                'amount': amount,
                'email': email,
                'address': address,
                'zip': zip,
                'city': city,
                'recurring_payment': recurring_payment,
                'number_of_months': number_of_months,
                'recurring_payment_expiration_date': expiration_date
            }
        )
    except Exception as e:
        print(e)
        return None
    return bounty_order