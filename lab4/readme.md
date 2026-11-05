Metoda	Ścieżka			Oczekiwany	Otrzymany	Status
------------------------------------------------------------------
GET     /projects               200             200             OK
POST    /projects               201             201             OK
POST    /projects               409             409             OK
GET     /users                  200             200             OK
GET     /tasks                  200             200             OK
POST    /tasks                  422             422             OK
DELETE  /projects/1             409             409             OK
