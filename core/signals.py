from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import Transfer, Notification, AccountFreeze, Deposit
from django.conf import settings
from .utils import send_html_email

@receiver(pre_save, sender=Transfer)
def refund_failed_transfer(sender, instance, **kwargs):
    """
    Signal to handle refund logic when a Transfer status changes to 'failed'.
    """
    if instance.pk:  # Check if this is an existing object (update)
        try:
            old_instance = Transfer.objects.get(pk=instance.pk)
            # Check if status is transitioning to 'failed' from something else
            if old_instance.status != 'failed' and instance.status == 'failed':
                
                # Refund the Sender
                sender_account = instance.account
                sender_account.account_balance += instance.amount
                sender_account.save()
                
                Notification.objects.create(
                    user=instance.user,
                    notification_type="Credit Alert",
                    amount=instance.amount,
                    transaction_id=instance.transaction_id,
                )

                # Send Refund Email
                try:
                    subject = f'Credit Alert: Refund +${instance.amount}'
                    message = f'Your transfer of ${instance.amount} (ID: {instance.transaction_id}) failed and has been refunded to your account.'
                    send_html_email(subject, [instance.user.email], {'subject_header': 'Credit Alert - Refund', 'message': message})
                except:
                    pass

                # Debit the Receiver (if internal and money was previously credited)
                # Note: Logic assumes money was credited on 'completed'. 
                # If transaction was "processing" or "pending" (external), receiver might not have funds yet.
                # However, for internal transfers, we often credit immediately or on 'completed'.
                # Let's check TransferProcess view: 
                # It credits receiver immediately if pin is correct and status becomes 'completed'.
                
                if instance.transfer_type == 'internal' and instance.receiver_account:
                    # Only debit if the status was previously 'completed' 
                    # OR if we want to be safe that funds were indeed added.
                    # Based on views.py, internal transfers get status='completed' on success.
                    # So if we are reversing a 'completed' transaction to 'failed':
                    if old_instance.status == 'completed':
                        receiver_account = instance.receiver_account
                        receiver_account.account_balance -= instance.amount
                        receiver_account.save()
                        
                        Notification.objects.create(
                            user=instance.receiver,
                            notification_type="Debit Alert", 
                            amount=instance.amount,
                            transaction_id=instance.transaction_id
                        )

        except Transfer.DoesNotExist:
            pass # Should not happen given instance.pk check

@receiver(pre_save, sender=Deposit)
def check_deposit_completion(sender, instance, **kwargs):
    """
    Signal to credit account when Deposit status changes to 'completed'.
    """
    if instance.pk: # Update
        try:
            old_instance = Deposit.objects.get(pk=instance.pk)
            # Check if status is transitioning to 'completed'
            if old_instance.status != 'completed' and instance.status == 'completed':
                account = instance.account
                account.account_balance += instance.amount
                account.save()
                
                Notification.objects.create(
                    user=instance.user,
                    notification_type="Credit Alert",
                    amount=instance.amount,
                    transaction_id=instance.transaction_id
                )

                # Send Email for admin approval
                try:
                    subject = f'Deposit Completed: +${instance.amount}'
                    message = f'Your deposit of ${instance.amount} has been successfully processed and credited to your account.\nTransaction ID: {instance.transaction_id}'
                    send_html_email(subject, [instance.user.email], {'subject_header': 'Deposit Completed', 'message': message})
                except:
                    pass
        except Deposit.DoesNotExist:
            pass
    else:
        # New instance
        # If created with 'completed' status directly (e.g. admin or script), credit it.
        if instance.status == 'completed':
            account = instance.account
            account.account_balance += instance.amount
            account.save()
            
            Notification.objects.create(
                user=instance.user,
                notification_type="Credit Alert",
                transaction_id=instance.transaction_id
            )
            
            # Send Email
            try:
                subject = f'Deposit Completed: +${instance.amount}'
                message = f'Your deposit of ${instance.amount} has been successfully processed and credited to your account.\nTransaction ID: {instance.transaction_id}'
                context = {
                    'subject_header': 'Deposit Completed',
                    'message': message
                }
                send_html_email(subject, [instance.user.email], context)
            except:
                pass

@receiver(post_save, sender=AccountFreeze)
def account_freeze_notification(sender, instance, created, **kwargs):
    try:
        user = instance.account.user
        recipient_list = [user.email]
        
        if created and instance.is_active:
             # Fresh Freeze
            subject = 'Urgent: Account Frozen'
            message = f'Your account has been frozen due to: {instance.get_reason_display()}.\n\nNotes: {instance.notes}\n\nPlease contact support immediately.'
            context = {
                'subject_header': 'Account Frozen',
                'message': message,
                'action_url': '#', # Ideally link to support
                'action_text': 'Contact Support'
            }
            send_html_email(subject, recipient_list, context)
            
        elif not instance.is_active and not created:
            # Unfreeze (Update)
            subject = 'Account Restored: Freeze Lifted'
            message = f'Good news! The freeze on your account has been lifted. You can now access your funds normally.'
            context = {
                'subject_header': 'Account Restored',
                'message': message  
            }
            send_html_email(subject, recipient_list, context)
            
    except Exception as e:
        print(f"Error sending email: {e}")
