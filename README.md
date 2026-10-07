# happyhue

```
python manage.py migrate
python manage.py seed_catalog
```

## 2. Firebase console
1. Create a project (or use one) at console.firebase.google.com.
2. Build > Authentication > Sign-in method > enable **Phone**.
3. Authentication > Settings > Authorized domains: add your live domain (`localhost` is there by default).
4. Project settings > General > Your apps > add a **Web app**. Copy `apiKey`, `authDomain`, `projectId`, `appId`.
   (The web apiKey is not a secret.)
5. Project settings > Service accounts > **Generate new private key**. Keep that JSON out of git.
6. While developing, Authentication > Sign-in method > Phone > *Phone numbers for testing* lets you use a fake
   number with a fixed code and send no real SMS.
7. Real SMS volume is limited on the free tier and may need a billing plan. Check Firebase's current pricing and
   India SMS rules before launch.

## razorpay

test card
```
Mastercard (domestic): 5267 3181 8797 5449
OTP: 123456
ccv: any 3 digit
expiry: any future date
```