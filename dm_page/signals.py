# from django.db.models.signals import m2m_changed, post_save, pre_save
# from django.dispatch import receiver
# from .models import Locked, Donation

# @receiver(post_save, sender=Locked)
# def post_save_lock(sender, instance, created, **kwargs):
# 	if created:
# 		to_lock = Donation.objects.all()
# 		instance.donation_list = None
# 		if instance.date_start != None:
# 			to_lock = to_lock.filter(date_donated__gte=instance.date_start)
# 		if instance.date_end != None:
# 			to_lock = to_lock.filter(date_donated__lte=instance.date_end)
# 		instance.donation_list = str(list([don.id for don in to_lock]))
# 		instance.save()
# 	else:
# 		pass # for pre_save

# @receiver(pre_save, sender=Locked)
# def pre_save_lock(sender, instance, **kwargs):
# 	if instance.id == None: # for post_save
# 		pass
# 	else:
# 		to_lock = Donation.objects.all()
# 		instance.donation_list = None
# 		if instance.date_start != None:
# 			to_lock = to_lock.filter(date_donated__gte=instance.date_start)
# 		if instance.date_end != None:
# 			to_lock = to_lock.filter(date_donated__lte=instance.date_end)
# 		instance.donation_list = str(list([don.id for don in to_lock]))
# 		if len(instance.contacts.all()) > 0:
# 			to_lock = to_lock.filter(contact__in=list(instance.contacts.all()))
# 			instance.donation_list = str(list([don.id for don in to_lock]))
# 		if len(instance.organisations.all()) > 0:
# 			to_lock = to_lock.filter(organisation__in=list(instance.organisations.all()))
# 			instance.donation_list = str(list([don.id for don in to_lock]))
# 		if len(instance.donation_types.all()) > 0:
# 			to_lock = to_lock.filter(donation_type__in=list(instance.donation_types.all()))
# 			instance.donation_list = str(list([don.id for don in to_lock]))

# @receiver(m2m_changed, sender=Locked.contacts.through)
# def m2m_changed_contacts(sender, instance, action, **kwargs):
# 	if len(list(instance.contacts.all())) > 0 and (action == "post_add" or action == "post_remove"):
# 		to_lock = Donation.objects.filter(id__in = eval(instance.donation_list))
# 		to_lock = to_lock.filter(contact__in=list(instance.contacts.all()))
# 		instance.donation_list = str(list([don.id for don in to_lock]))
# 		instance.save()

# @receiver(m2m_changed, sender=Locked.organisations.through)
# def m2m_changed_organisations(sender, instance, action, **kwargs):
# 	if len(list(instance.organisations.all())) > 0 and (action == "post_add" or action == "post_remove"):
# 		to_lock = Donation.objects.filter(id__in = eval(instance.donation_list))
# 		to_lock = to_lock.filter(organisation__in=list(instance.organisations.all()))
# 		instance.donation_list = str(list([don.id for don in to_lock]))
# 		instance.save()

# @receiver(m2m_changed, sender=Locked.donation_types.through)
# def m2m_changed_donation_types(sender, instance, action, **kwargs):
# 	if len(list(instance.donation_types.all())) > 0 and (action == "post_add" or action == "post_remove"):
# 		to_lock = Donation.objects.filter(id__in = eval(instance.donation_list))
# 		to_lock = to_lock.filter(donation_type__in=list(instance.donation_types.all()))
# 		instance.donation_list = str(list([don.id for don in to_lock]))
# 		instance.save()


	# def delete(self, *args, **kwargs):
	# 	uniq = set(list(chain(*[eval(previous_locks.donation_list) for previous_locks in Locked.objects.exclude(id=self.id)])))
	# 	print("Uniq: ", uniq)
	# 	to_remove_lock = list(set(eval(self.donation_list)).difference(uniq))
	# 	print("To Remove: ", to_remove_lock)
	# 	for i in to_remove_lock:
	# 		donation = Donation.objects.get(id=i)
	# 		donation.locked = False
	# 		donation.save()
	# 	super(Locked, self).delete(*args, **kwargs)