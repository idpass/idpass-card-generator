# Card Endpoints (v1)


## Upload card templates
_[api/v1/cards/](http://localhost:8000/api/v1/cards/)_

In this example, we are using the existing templates in our test directory. Before you create a custom template, please check [Preparing the templates](#Preparing-the-templates) section.
```http request
POST http://localhost:8000/api/v1/cards/
Content-Type: multipart/form-data; boundary=WebAppBoundary
Authorization: Token <auth_token>

--WebAppBoundary
Content-Disposition: form-data; name="title"

# Value of title
Card Template
--WebAppBoundary
Content-Disposition: form-data; name="front_svg"; filename="front_card.svg"
Content-Type: application/json

< ./card_generator/api/tests/v1/cards/samples/front_card.svg
--WebAppBoundary--
Content-Disposition: form-data; name="back_svg"; filename="back_svg.svg"
Content-Type: application/json

< ./card_generator/api/tests/v1/cards/samples/back_card.svg
--WebAppBoundary--
```

The response will give us an idea where is the location of our templates and the uuid.
We will use the uuid in retrieving the fields and rendering the cards.
```http response
{
  "front_svg": "/media/cards/front_card.svg",
  "back_svg": "/media/cards/back_svg.svg",
  "title": "Card Template",
  "uuid": "a8f097eb-04de-4638-9b33-f08cf3897169"
}
```

## Get the templates
_[api/v1/cards/](http://localhost:8000/api/v1/cards/)_

```http request
GET http://localhost:8000/api/v1/cards
Content-Type: application/json
Authorization: Token <auth_token>
```

We are expecting a list of templates as the response

```http response
[
  {
    "front_svg": "/media/cards/front_card.svg",
    "back_svg": "/media/cards/back_svg.svg",
    "title": "Card Template",
    "uuid": "a8f097eb-04de-4638-9b33-f08cf3897169"
  }
]
```

## Retrieving the fields
_[api/v1/cards/\<uuid>/fields/](http://localhost:8000/api/v1/cards/<uuid>/fields/)_

In order for us to render the cards, we will need to add values to the variable fields in the template.

```http request
GET http://localhost:8000/api/v1/cards/a8f097eb-04de-4638-9b33-f08cf3897169/fields
Content-Type: application/json
Authorization: Token <auth_token>
```

This will give us a list of the available fields we can provide a value to.

```http response
{
  "fields": [
    {
      "tag": "image",
      "name": "profile_svg_3"
    },
    {
      "tag": "text",
      "name": "nationality"
    },
    {
      "tag": "text",
      "name": "date_of_birth"
    },
    {
      "tag": "text",
      "name": "date_of_issue"
    },
    {
      "tag": "text",
      "name": "identification_no"
    },
    {
      "tag": "text",
      "name": "surname"
    },
    {
      "tag": "text",
      "name": "given_name"
    },
    {
      "tag": "text",
      "name": "date_of_expiry"
    },
    {
      "tag": "text",
      "name": "sex"
    },
    {
      "tag": "image",
      "name": "qrcode_svg_15"
    }
  ]
}
```

## Rendering the cards
_[api/v1/cards/\<uuid>/render/](http://localhost:8000/api/v1/cards/<uuid>/render/)_

Render the cards with the user's information. To add an image, e.g. for `profile_svg_3`, encode in base64 and format to data uri like this `data:image/jpg;base64,<base64 string>`

```http request
POST http://localhost:8000/api/v1/cards/a8f097eb-04de-4638-9b33-f08cf3897169/render/
Content-Type: application/json
Authorization: Token <auth_token>

{
  "fields": {
    "given_name": "John",
    "surname": "Doe",
    "nationality": "American",
    "sex": "Male",
    "date_of_issue":"Jan 1, 2022",
    "date_of_expiry": "Jan 1, 2022",
    "date_of_birth": "Jan 1, 2022",
    "identification_no": "00000000001",
    "qrcode_svg_15": "00000000001",
    "profile_svg_3": "data:image/jpg;base64,<base64 string>"
  }
}
```
 Response looks like this

```http response
{
  "files": {
    "pdf": "data:application/pdf;base64,<base64 string>",
    "png": [
      "data:image/png;base64,<base64 string>",
      "data:image/png;base64,<base64 string>"
    ]
  }
}
```

An example of a rendered card ID

![IDPASS FRONT CARD](../../tests/v1/cards/samples/idpass_front.png)
![IDPASS BACK CARD](../../tests/v1/cards/samples/idpass_back.png)


### Preparing the templates

The card templates should be created or prepared in a way that the generator can understand. The most important piece is the variables.
The system finds all the variables in the template to provide you a list of fields and apply the values provided during render.

##### text
- Text related variables are expected to use `text` tag and enclose the variable name in double brackets `{{ }}`
```svg
<text id="svg_5">{{ identification_no }}</text>
```
```
Field endpoint response
{
    "name": "identification_no",
    "tag": "text"
}

Sample render value
{
    "fields": {
        "identification_no": "00000000001"
    }
}
```

##### image
- Images are expected to use `image` tag with `data-variable` attribute to mark the variable name. During render, the system will look for `xlink:href` attribute and inject the value. Images are expected to be embedded as a data uri.
```svg
<image data-variable="profile_svg_3" xlink:href="data:image/svg+xml; charset=utf8, <base64 string>"/>
```
```
Field endpoint response
{
    "name": "profile_svg_3",
    "tag": "image"
}

Sample render value
{
    "fields": {
        "profile_svg_3": "data:image/jpg;base64,<base64 string>"
    }
}
```

##### qrcode
- QR codes are also images but accepts any string values. If your variable name starts with the word `qrcode`, the system can create a QR code based on the given values.
- Users can still use `image` tag and a different variable name while providing a data uri format qrcode.
- During render, if the user passed `create_qr_code: false` in the payload, the system will not generate any QR code and will use the provided value instead.

```svg
<image data-variable="qrcode_svg_15" id="svg_15" xlink:href="data:image/svg+xml; charset=utf8,<base64 string>"/>
```
