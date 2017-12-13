import os

class ManageDownloads:

	current_dir
	current_name
	dest_dir
	final_name

	def getUserPreference(self):
		print('Enter the current location of the downloaded file : ')
		self.current_dir = input()
		print('Enter the current name of the downloaded file : ')
		self.current_name = input()
		print('Enter the desired destination directory of the downloaded file : ')
		self.dest_dir = input()
		print('Enter the desired name of the downloaded file : ')
		self.final_name = input()


	def rename(self):
		old_file = os.path.join(self.current_dir, self.current_name)
		new_file = os.path.join(self.dest_dir, self.final_name)
		os.rename(old_file, new_file)
		return new_file