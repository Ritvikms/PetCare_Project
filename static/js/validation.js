$(document).ready(function () {
  //Custom method for date comparison
  jQuery.validator.addMethod(
    "greaterThan",
    function (value, element, params) {
      if (!/Invalid|NaN/.test(new Date(value))) {
        return new Date(value) > new Date($(params).val());
      }

      return (
        (isNaN(value) && isNaN($(params).val())) ||
        Number(value) > Number($(params).val())
      );
    },
    "Must be greater than {0}."
  );

  // Custom methods only for letters
  jQuery.validator.addMethod(
    "lettersonly",
    function (value, element) {
      return this.optional(element) || /^[a-z\s]+$/i.test(value);
    },
    "Only alphabetical characters"
  );

  $("#hostProfile").validate();

  $("#profile").validate();

  $("#login").validate();

  $("#creditCard").validate({
    rules: {
      card_holder: {
        lettersonly: true,
      },
      card_number: {
        number: true,
        min: 1111111111111111 + Number.MIN_VALUE,
      },
      cvv: {
        number: true,
      },
    },
    messages: {
      card_number: {
        minlength: "Please enter 16 digt number",
        min: "Value Should be between 1111 1111 1111 1111 and 9999 9999 9999 9999",
      },
    },
  });

  $("#updateCommission").validate({
    rules: {
      commission_percentage: {
        number: true,
      },
    },
  });

  $("#checkAvailability").validate({
    rules: {
      check_out: { greaterThan: "#check_in" },
    },
  });

  $("#serviceProviderRegForm").validate({
    rules: {
      email: {
        email: true,
        remote: {
          url: "/is-provider-email-exist",
          type: "get",
        },
      },
    },
    messages: {
      email: {
        remote: "Email provided is already registered",
      },
      phone: {
        remote: "This Phone number is already registered",
      },
    },
  });

  $("#userRegistration").validate({
    rules: {
      email: {
        email: true,
        remote: {
          url: "/is-user-email-exist",
          type: "get",
        },
      },
      contact_no: {
        remote: {
          url: "/is-user-phone-exist",
          type: "get",
        },
      },
      password: {
        minlength: 3,
      },
      confirm_password: {
        minlength: 3,
        equalTo: "#password",
      },
    },
    messages: {
      email: {
        remote: "Email provided is already registered",
      },
      contact_no: {
        remote: "This Phone number is already registered",
      },
      confirm_password: {
        equalTo: "Password and confirm password doesn't match",
      },
    },
  });

  $("#admin-change-password").validate({
    rules: {
      password: {
        minlength: 3,
      },
      confirm_password: {
        minlength: 3,
        equalTo: "#password",
      },
    },
    messages: {
      confirm_password: {
        equalTo: "Password and confirm password doesn't match",
      },
    },
  });

  $("#changePassword").validate({
    rules: {
      password: {
        minlength: 3,
      },
      confirm_password: {
        minlength: 3,
        equalTo: "#password",
      },
    },
    messages: {
      confirm_password: {
        equalTo: "Password and confirm password doesn't match",
      },
    },
  });

  $("#regForm").validate({
    rules: {
      email: {
        email: true,
        remote: {
          url: "is-user-email-exist",
          type: "get",
        },
      },
      password: {
        minlength: 3,
      },
      confirm_password: {
        minlength: 3,
        equalTo: "#password",
      },
    },
    messages: {
      email: {
        remote: "Email already registered",
      },
      confirm_password: {
        equalTo: "Password and confirm password doesn't match",
      },
    },
  });
});
