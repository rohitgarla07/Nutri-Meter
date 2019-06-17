var AWS = require('aws-sdk');
AWS.config.update({region: 'us-east-1'});
var lexruntime = new AWS.LexRuntime();

exports.handler = (event, context, callback) => {
    try {
        // By default, treat the user request as coming from the America/New_York time zone.
        var userInput = event.messages;
        // var refId = event.refid;
        var params = {
            botAlias: '$LATEST', /* required, has to be '$LATEST' */
            botName: 'nutrimeterchat',  /* enter the name of the lex */
            inputText: userInput, /* required, your text */
            userId: '1234', /* required, arbitrary identifier */
            sessionAttributes: {
            someKey: 'STRING_VALUE',
        }

    };

    lexruntime.postText(params, function(err, data) {
        if (err) console.log(err); // an error occurred
        else callback(null, data.message);           // successful response
    });
    } catch (err) {
        console.log(err);
    }
};