from django.dispatch import receiver
from invitations.signals import invite_accepted


@receiver(invite_accepted)
def invitation_accepted(sender, **kwargs):
    # This code will run when an invitation is accepted
    print("Invitation accepted!")
