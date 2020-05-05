from bunq import ApiEnvironmentType, Pagination
from bunq.sdk.model.generated import endpoint
from bunq.sdk.context.api_context import ApiContext
from bunq.sdk.context.bunq_context import BunqContext

from config import Configuration
from logger import configure_logger

LOGGER = configure_logger(__name__)

account_path = {
    'MonetaryAccountJoint': 'monetary-account-joint',
    'MonetaryAccountBank': 'monetary-account-bank',
    'MonetaryAccountSavings': 'monetary-account-savings',
}


class BunqApi:
    API_CONTEXT_FILE_PATH = 'bunq-production.conf'
    DEVICE_DESCRIPTION = 'BUNQ_YNAB_AWS'

    def __init__(self, config_location):
        self.user = None
        self.config = Configuration(config_location)
        self.setup_context()
        self.setup_current_user()

    def setup_context(self):
        if 'bunq-conf' in self.config.value:
            LOGGER.debug('Found existing api context config. Restoring.')
            api_context = ApiContext.from_json(self.config.value['bunq-conf'])
            api_context.ensure_session_active()
        else:
            LOGGER.debug('Did not find existing api context config. creating.')
            api_context = ApiContext.create(
                ApiEnvironmentType.PRODUCTION,
                self.config.value['bunq']['api_token'],
                self.DEVICE_DESCRIPTION
            )
            self.config.value['bunq-conf'] = api_context.to_json()
            LOGGER.info('persisting new api context config')
            self.config.save(self.config.value)

        BunqContext.load_api_context(api_context)

    def setup_current_user(self):
        user = endpoint.User.get().value
        if (isinstance(user, endpoint.User)):
            self.user = user
            LOGGER.info('set current user on {0} '.format(user.UserPerson.display_name))
        else:
            # TODO throw exception
            LOGGER.error('Could not set user with this response')

    def print_accounts(self, userid):
        pass
        # payment_id = endpoint.MonetaryAccount.list(
        #
        # )

        # TODO vervangen met sdk call

        # method = 'v1/user/{0}/monetary-account'.format(userid)
        # for a in self.get(method):
        #     for k, v in a.items():
        #         LOGGER.info("  {0:28}  {1:10,} {2:3}  ({3})".format(
        #             v["description"],
        #             Decimal(v["balance"]["value"]),
        #             v["balance"]["currency"],
        #             v["id"]))

    def list_users(self):
        users = endpoint.User.list().value

        for k, user in users:
            LOGGER.info('{0} "{1}" ({2})'.format(k, user.display_name, user.uuid))
            self.print_accounts(user.id)

    def get_user_id(self):
        pass

        # TODO vervangen met sdk call

        # for u in self.get('v1/user'):
        #     for k, v in u.items():
        #         if (v["display_name"].casefold() == user_name.casefold() or
        #                 str(v["id"]) == user_name):
        #             return str(v["id"])
        # raise Exception("BUNQ user '{0}' not found".format(user_name))

    def get_account_type(self, user_id, account_id):
        pass

        # TODO vervangen met sdk call

        # reply = self.get('v1/user/{0}/monetary-account/{1}'.format(
        #     user_id, account_id))
        # return next(iter(reply[0]))

    def get_account_id(self, account_name):
        accounts = endpoint.MonetaryAccount.list({'display_name': account_name})
        for account in accounts.value:
            if account_name == account.get_referenced_object().description:
                return account.get_referenced_object()
        LOGGER.error('Could not find account with name {0}'.format(account_name))

        # TODO vervangen met sdk call

        # reply = self.get('v1/user/{0}/monetary-account'.format(user_id))
        # for entry in reply:
        #     account_type = next(iter(entry))
        #     account = entry[account_type]
        #     if (account["description"].casefold() == account_name.casefold() or
        #             str(account["id"]) == account_name):
        #         return str(account["id"])
        # raise Exception("BUNQ account '{0}' not found".format(account_name))

    def get_callbacks(self, user_id, account_id):
        pass

        # TODO vervangen met sdk call

        # method = 'v1/user/{0}/monetary-account/{1}'.format(user_id, account_id)
        # result = self.get(method)[0]
        # account_type = next(iter(result))
        # return result[account_type]["notification_filters"]

    def put_callbacks(self, user_id, account_id, new_notifications):
        pass

        # TODO vervangen met sdk call

        # data = {
        #     "notification_filters": new_notifications
        # }
        # account_type = self.get_account_type(user_id, account_id)
        # method = 'v1/user/{}/{}/{}'.format(
        #     user_id, self.get_path(account_type), account_id)
        # self.put(method, data)

    def get_transactions(self, account):
        pagination = Pagination()
        pagination.count = 100
        payments_response = endpoint.Payment.list(account.id_,params=pagination.url_params_count_only)

        print("Translating payments...")
        transactions = []
        first_day = None
        last_day = None
        unsorted_payments = payments_response.value
        payments = sorted(unsorted_payments, key=lambda payment: payment.created)
        for payment in payments:
            if payment.amount.currency != "EUR":
                raise Exception("Non-euro payment: " + payment.amount.currency)
            date = payment.created[:10]
            if not first_day or date < first_day:
                first_day = date
            if not last_day or last_day < date:
                last_day = date

            transactions.append({
                "amount": payment.amount.value,
                "date": date,
                "payee": payment.counterparty_alias.pointer.name,
                "description": payment.description
            })

        # For correct duplicate calculation, return only complete days
        return [t for t in transactions
                if first_day < t["date"] or t["date"] == last_day]
